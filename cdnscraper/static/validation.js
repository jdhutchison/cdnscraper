/**
 * Checks of the value of the domain field is a valid FQDN.
 * @return (boolean) True if domain value is valid.
 */
function validateDomain() {
    var domain = document.getElementById('domain').value;

    if (!domain) {
        alert('You must enter a valid domain name')
        return false;
    }

    // Strip out scheme from URL if present
    var schemeEndPoint = domain.indexOf('://');
    if (schemeEndPoint > -1) {
        domain = domain.substring(schemeEndPoint + 3);
        document.getElementById('domain').value = domain;
    }

    if (!/^([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)+[a-zA-Z]{2,}(?:\.[a-z]{2})?$/.test(domain)) {
        alert('The domain you entered is not valid')
        return false;
    }
    return true;
}