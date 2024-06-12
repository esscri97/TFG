function validatePassword() {
    var password = document.getElementById("password").value;

    // Expresión regular para validar la contraseña
    var passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[\W_]).{8,}$$/;

    if (!passwordRegex.test(password)) {
        // Muestra el mensaje de error en el documento
        document.getElementById("password-error").textContent = "La contraseña debe tener al menos 8 caracteres, una letra, un número y un símbolo.";
        return false;
    } else {
        // Limpia el mensaje de error si la contraseña es válida
        document.getElementById("password-error").textContent = "";
    }

    return true;
}

const togglePassword = document.querySelector('#togglePassword');
        const password = document.querySelector('#password');

        togglePassword.addEventListener('click', function (e) {
            // toggle the type attribute
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
        });