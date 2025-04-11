// Notification Manager for web push notifications
const NotificationManager = {
  isSupported: () => {
    return 'serviceWorker' in navigator && 'PushManager' in window;
  },

  requestPermission: async () => {
    if (!NotificationManager.isSupported()) {
      console.warn('Push notifications are not supported in this browser');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  },

  registerServiceWorker: async () => {
    if (!NotificationManager.isSupported()) {
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js');
      return registration;
    } catch (error) {
      console.error('Service worker registration failed:', error);
      return null;
    }
  },

  subscribeToPushNotifications: async (subscriptionUrl) => {
    try {
      const permission = await NotificationManager.requestPermission();
      if (!permission) {
        console.warn('Notification permission denied');
        return null;
      }

      const registration = await NotificationManager.registerServiceWorker();
      if (!registration) {
        return null;
      }

      // Get the push subscription
      let subscription = await registration.pushManager.getSubscription();
      if (!subscription) {
        // Create a new subscription
        const response = await fetch(subscriptionUrl);
        const vapidPublicKey = await response.json();
        
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: vapidPublicKey
        });
      }

      return subscription;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      return null;
    }
  }
};

export default NotificationManager;
