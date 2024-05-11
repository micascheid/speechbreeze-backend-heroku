import os

from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import stripe
from app.database.models import Slp

load_dotenv()
stripe_sk = os.getenv('STRIPE_SK')

stripe_bp = Blueprint('stripe', __name__)

endpoint_secret = 'whsec_0a951e68b79db3f2e7300818967690b173c05992f22c9f288deb33af0286046e'

subscription_plan = {
    'price_1PCmW7EnGNPnb7LNPGcI2MY7': 1,
    'price_1PCmWXEnGNPnb7LNxwmGRBTL': 2
}

@stripe_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Bad payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Bad signature', 400

    event_type = event['type']

    if event_type in event_handlers:
        event_handlers[event_type](event)
    else:
        return 'Unhandled event type', 400

    return jsonify(success=True)


def handle_charge_succeeded(event):
    print('Handling charge.succeeded:', event)


def handle_customer_created(event):
    print('Handling customer.created:', event)
    try:
        email = event['data']['object']['email']
        cus_id = event['data']['object']['id']
        slp = Slp.query.filter_by(email=email).first()
        slp_id = slp.slp_id

        if not slp:
            raise Exception(f"User purchase Email: {email}, was not found")

        Slp.update_slp(slp_id=slp_id, stripe_id=cus_id)

    except Exception as e:
        print("Error handling stripe customer created: " + str(e))


def handle_payment_method_attached(event):
    print('Handling payment_method.attached:', event)


def handle_customer_updated(event):
    print('Handling customer.updated:', event)


def handle_customer_subscription_created(event):
    print('Handling customer.subscription.created:', event)


def handle_customer_subscription_updated(event):
    print('Handling customer.subscription.updated:', event)
    try:
        cus_id = event['data']['object']['customer']
        sub_start = event['data']['object']['current_period_start']
        sub_end = event['data']['object']['current_period_end']
        email = event['data']['object']['customer_email']
        slp = Slp.query.filter_by(stripe_id=cus_id).first()

        if not slp:
            raise Exception(f"Unable to find slp with Customer ID: {cus_id}")

        Slp.update_slp(email=email, sub_start=sub_start, sub_end=sub_end)

    except Exception as e:
        print("Error handling stripe customer created: " + str(e))
        raise Exception(f"Failed to update user with error: {e}")


def handle_payment_intent_succeeded(event):
    print('Handling payment_intent.succeeded:', event)


def handle_payment_intent_created(event):
    print('Handling payment_intent.created:', event)


def handle_invoice_created(event):
    print('Handling invoice.created:', event)


def handle_invoice_finalized(event):
    print('Handling invoice.finalized:', event)


def handle_invoice_updated(event):
    print('Handling invoice.updated:', event)


def handle_invoice_paid(event):
    print('Handling invoice.paid:', event)


def handle_invoice_payment_succeeded(event):
    print('Handling invoice_payment_succeeded:', event)
    try:
        # 19.99 a month: price_1P6bKJEnGNPnb7LNoiy3zl6O,
        # 99.99 a year: price_1P8vBPEnGNPnb7LN6BypIpUU

        email = event['data']['object']['customer_email']
        cus_id = event['data']['object']['customer']
        first_line_item = event['data']['object']['lines']['data'][0]
        sub_start = first_line_item['period']['start']
        sub_end = first_line_item['period']['end']
        product = first_line_item['plan']['id']
        sub_type = subscription_plan.get(product)
        slp = Slp.query.filter_by(stripe_id=cus_id).first()
        if slp is None:
            slp = Slp.query.filter_by(email=email).first()

        slp_id = slp.slp_id

        if not slp:
            raise Exception(f"Unable to find slp with Customer ID: {cus_id}")

        Slp.update_slp(slp_id=slp_id, stripe_id=cus_id, sub_start=sub_start, sub_end=sub_end, sub_type=sub_type)

    except Exception as e:
        print(f"Failed to update invoice.payment_succeeded: {e}")
        raise Exception(f"Failed to update invoice.payment_succeeded: {e}")


def handle_checkout_session_completed(event):
    print('Handling checkout.session.completed:', event)
    try:
        email = event['data']['object']['customer_email']
        stripe_id = event['data']['object']['customer']

        Slp.update_slp(email=email, stripe_id=stripe_id)
    except Exception as e:
        print(f"Failed to handle checkout session completed: {e}")
        raise Exception(f"Failed to handle checkout session completed: {e}")

event_handlers = {
    'invoice.payment_succeeded': handle_invoice_payment_succeeded,
    'checkout.session.completed': handle_checkout_session_completed,
    # 'handle_customer_subscription_updated': handle_customer_subscription_updated,
}

# event_handlers = {
#     'charge.succeeded': handle_charge_succeeded,
#     'customer.created': handle_customer_created,
#     'payment_method.attached': handle_payment_method_attached,
#     'customer.updated': handle_customer_updated,
#     'customer.subscription.created': handle_customer_subscription_created,
#     'customer.subscription.updated': handle_customer_subscription_updated,
#     'payment_intent.succeeded': handle_payment_intent_succeeded,
#     'payment_intent.created': handle_payment_intent_created,
#     'invoice.created': handle_invoice_created,
#     'invoice.finalized': handle_invoice_finalized,
#     'invoice.updated': handle_invoice_updated,
#     'invoice.paid': handle_invoice_paid,
#     'invoice.payment_succeeded': handle_invoice_payment_succeeded,
#     'checkout.session.completed': handle_checkout_session_completed
# }

'''
customer.created Done
customer.subscription.updated Done
invoice.payment_succeeded
checkout.session.completed
'''