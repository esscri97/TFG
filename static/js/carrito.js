function handlePurchase() {
    // Abrir la página de PayPal en una nueva pestaña
    window.open('https://www.paypal.com/es/home', '_blank');
    // Dejar que el formulario se envíe y redirija a la página de agradecimiento
    return true;
}