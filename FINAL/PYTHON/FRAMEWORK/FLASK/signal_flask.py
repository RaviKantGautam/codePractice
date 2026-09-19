from flask import Flask, request, jsonify
from blinker import Namespace
app = Flask(__name__)
my_signals = Namespace()
my_signal = my_signals.signal('my-signal')

'''
Signals

The following signals are sent:
1. request_started is sent before the before_request() functions are called.
2. request_finished is sent after the after_request() functions are called.
3. got_request_exception is sent when an exception begins to be handled, but before an errorhandler() is looked up or called.
4. request_tearing_down is sent after the teardown_request() functions are called.
'''

@app.route('/trigger-signal', methods=['POST'])
def trigger_signal():
    my_signal.send()
    return jsonify({"message": "Signal triggered"}), 200

if __name__ == '__main__':
    app.run(debug=True)