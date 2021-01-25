from datetime import datetime
from flask import Flask, request, jsonify
from marshmallow import fields, Schema, validate


app = Flask(__name__)

now = datetime.now()


class Requiredfields(Schema):
    """ Fields which are required for entering the credit card details"""
    creditCardNumber = fields.Str(required=True)
    CardHolder = fields.Str(required=True)
    ExpirationDate = fields.Date('%d-%m-%Y', required=True, validate=lambda x: x > now)
    SecurityCode = fields.Str(validate=validate.Length(equal=3))
    Amount = fields.Float(required=True, validate=validate.Range(min=0))


def validate_creditCardNumber(data):
    """ validating the credit card number entered by the user"""
    if len(data) == 16:
        digits = [int(c) for c in data if c.isdigit()]
        checksum = digits.pop()
        digits.reverse()
        doubled = [2 * d for d in digits[0::2]]
        total = sum(d - 9 if d > 9 else d for d in doubled) + sum(digits[1::2])
        if (total * 9) % 10 != checksum:
            raise ValueError("Credit Card is not valid")
    else:
        raise ValueError("The length of credit card number is incorrect")

mandatory_fields = Requiredfields()


@app.route('/ProcessPayment', methods=['POST'])
def process_payment():
    json_data = request.get_json()
    try:
        validate_creditCardNumber(json_data['creditCardNumber']) # validating credit card number
    except Exception as e:
        return str(e), 400

    payment_gateway_service_call = PaymentGateway.payment_gateway(json_data())
    try:
        if payment_gateway_service_call['Status'] == 1:
            return "Payment is Processed", 200  # Ok
        else:
            return "Payment is Failed", 400
    except Exception as e:
        return "Internal Server Error", 500


class PaymentGateway:
    """ Where we will call all the payment gateway """
    CHEAP = "URL"
    EXPENSIVE = "URL"
    PREMIUM = "URL"

    @classmethod
    def payment_gateway(cls, data):
        # taking all the values so that it can used while calling to any of the gateway
        try:
            if data['Amount'] < 20:
                PaymentGateway.use_external_service(cls.CHEAP, data)
            elif 21 < data['Amount'] < 500:
                PaymentGateway.check_availability(cls.EXPENSIVE)
                if 'response_of_expensive_gateway_call' == 0:
                    PaymentGateway.use_external_service(cls.CHEAP, data)
            else:
                PaymentGateway.use_external_service(cls.PREMIUM, data)
                if "response_of_premium_gateway" != 1:
                    for ping in range(1, 2):
                        if 'response_to_premium_gateway' == 0:
                            PaymentGateway.use_external_service(cls.PREMIUM, data)  # calling premium gateway
                        else:
                            break
            return {'Status': 1, "message": "Payment is processed successfully"}
        except Exception as e:
            return {'Status': 0, 'message': str(e)}

    @staticmethod
    def check_availability(url):
        """checking for a particular gateway is available or not"""
        pass

    @staticmethod
    def use_external_service(url, data):
        """using this method for calling a particular payment gateway"""
        pass


if __name__ == '__main__':
    app.run(debug=True)
