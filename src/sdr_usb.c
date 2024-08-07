// 
//  Pocket SDR C library - USB Device Functions.
//
//  Author:
//  T.TAKASU
//
//  History:
//  2021-10-20  0.1  new
//  2022-01-04  0.2  support CyUSB on Windows
//  2022-05-23  0.3  change coding style
//  2022-08-08  1.0  support multiple contexts for libusb-1.0
//  2024-06-29  1.1  change API sdr_usb_open()
//
#include "pocket_sdr.h"

// constants and macros --------------------------------------------------------
#ifndef WIN32
#define USB_VR          (LIBUSB_RECIPIENT_DEVICE | LIBUSB_REQUEST_TYPE_VENDOR)
#define USB_VR_IN       (USB_VR | LIBUSB_ENDPOINT_IN)
#define USB_VR_OUT      (USB_VR | LIBUSB_ENDPOINT_OUT)
#define TO_TRANSFER     15000    // USB transfer timeout (ms)
#endif

//------------------------------------------------------------------------------
//  Open USB device.
//
//  args:
//      bus         (I)   USB bus number  (-1: any)
//      port        (I)   USB port number (-1: any)
//      vid         (I)   USB device vendor IDs
//      pid         (I)   USB device product IDs
//      n           (I)   numboer of vid and pid
//
//  return
//      USB device (NULL: error)
//
sdr_usb_t *sdr_usb_open(int bus, int port, const uint16_t *vid,
    const uint16_t *pid, int n)
{
#ifdef WIN32
    sdr_usb_t *usb = new CCyUSBDevice();
    
    for (int i = 0; i < usb->DeviceCount(); i++) {
        usb->Open(i);
        for (int j = 0; j < n; j++) {
            if ((bus < 0 || usb->USBAddress == bus) &&
                usb->VendorID == vid[j] && usb->ProductID == pid[j]) {
                return usb;
            }
        }
        usb->Close();
    }
    delete usb;
    return NULL;
#else
    libusb_device **devs;
    struct libusb_device_descriptor desc;
    sdr_usb_t *usb = (sdr_usb_t *)sdr_malloc(sizeof(sdr_usb_t));
    int i, j, ndev, ret;
    
    if ((ret = libusb_init(&usb->ctx))) {
        fprintf(stderr, "libusb_init error (%d)\n", ret);
        sdr_free(usb);
        return NULL;
    }
    if ((ndev = libusb_get_device_list(usb->ctx, &devs)) <= 0) {
        fprintf(stderr, "USB device list get error.\n");
        libusb_exit(usb->ctx);
        sdr_free(usb);
        return NULL;
    }
    for (i = 0; i < ndev; i++) {
        if (libusb_get_device_descriptor(devs[i], &desc) < 0) continue;
        if ((bus >= 0 && bus != libusb_get_bus_number(devs[i])) ||
            (port >= 0 && port != libusb_get_port_number(devs[i]))) continue;
        for (j = 0; j < n; j++) {
            if (vid[j] == desc.idVendor && pid[j] == desc.idProduct) break;
        }
        if (j < n) break;
    }
    if (i >= ndev) {
        libusb_free_device_list(devs, 1);
        libusb_exit(usb->ctx);
        sdr_free(usb);
        return NULL;
    }
    if (libusb_open(devs[i], &usb->h)) {
        libusb_free_device_list(devs, 1);
        libusb_exit(usb->ctx);
        sdr_free(usb);
        return NULL;
    }
    libusb_free_device_list(devs, 1);
    libusb_claim_interface(usb->h, SDR_DEV_IF);
    return usb;
#endif // WIN32
}

//------------------------------------------------------------------------------
//  Close USB device.
//
//  args:
//      usb         (I)   USB device
//
//  return
//      none
//
void sdr_usb_close(sdr_usb_t *usb)
{
#ifdef WIN32
    usb->Close();
    delete usb;
#else
    libusb_release_interface(usb->h, SDR_DEV_IF);
    libusb_close(usb->h);
    libusb_exit(usb->ctx);
    sdr_free(usb);
#endif // WIN32
}

//------------------------------------------------------------------------------
//  Send vendor request to USB device.
//
//  args:
//      usb         (I)   USB device
//      mode        (I)   direction (0:IN,1:OUT)
//      req         (I)   USB vendor request
//      val         (I)   USB vendor request wValue
//      data        (IO)  data
//      size        (I)   data size (bytes) (size <= 64)
//
//  return
//      status (1: OK, 0: error)
//
int sdr_usb_req(sdr_usb_t *usb, int mode, uint8_t req, uint16_t val,
        uint8_t *data, int size)
{
    if (size > 64) return 0;
    
#ifdef WIN32
    CCyControlEndPoint *ep = usb->ControlEndPt;
    long len = size;
    
    ep->Target    = TGT_DEVICE;
    ep->ReqType   = REQ_VENDOR;
    ep->Direction = mode ? DIR_TO_DEVICE : DIR_FROM_DEVICE;
    ep->ReqCode   = req;
    ep->Value     = val;
    ep->Index     = 0;
    return ep->XferData(data, len);
#else
    if (libusb_control_transfer(usb->h, mode ? USB_VR_OUT : USB_VR_IN, req, val,
            0, data, size, TO_TRANSFER) < size) {
        return 0;
    }
    return 1;
#endif /* WIN32 */
}
