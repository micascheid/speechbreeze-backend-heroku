from app import create_app
import ssl
from werkzeug.serving import run_simple
app = create_app()

if __name__ == "__main__":
    # app.run()


    #local stuff
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

    # Load the cert and key, supplying the necessary passphrase
    context.load_cert_chain(certfile='/Users/micalinscheid/Documents/SpeechBreeze/localhttps/cert.pem',
                            keyfile='/Users/micalinscheid/Documents/SpeechBreeze/localhttps/key.pem',
                            password='localhttps')

    run_simple('0.0.0.0', 5000, app, ssl_context=context)