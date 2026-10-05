// Auto-dismiss flash messages after FLASH_TIMEOUT_MS (at least 3 seconds).
// Users can also close them at any time with the close button.
(function () {
    var FLASH_TIMEOUT_MS = 6000;

    document.querySelectorAll(".flash-message").forEach(function (el) {
        setTimeout(function () {
            if (!el.isConnected) {
                return;
            }
            if (window.bootstrap && window.bootstrap.Alert) {
                window.bootstrap.Alert.getOrCreateInstance(el).close();
            } else {
                el.remove();
            }
        }, FLASH_TIMEOUT_MS);
    });
})();
