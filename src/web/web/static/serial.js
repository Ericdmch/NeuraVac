const {useState} = React;

function SerialConsole() {
  const [serialData, setSerialData] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submitSerial(event) {
    event.preventDefault();
    const data = serialData.trim();

    if (!data || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch('/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data}),
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Unable to submit serial data');
      }

      setSerialData('');
      setMessage(`Submitted: ${result.message}`);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return React.createElement(
    'main',
    {className: 'console'},
    React.createElement('p', {className: 'eyebrow'}, 'NEURAVAC / SERIAL LINK'),
    React.createElement('h1', null, 'Serial Console'),
    React.createElement(
      'p',
      {className: 'description'},
      'Send a sequence of serial values to the robot.'
    ),
    React.createElement(
      'form',
      {className: 'serial-form', onSubmit: submitSerial},
      React.createElement('label', {htmlFor: 'serial-input'}, 'Serial data'),
      React.createElement(
        'div',
        {className: 'input-row'},
        React.createElement('input', {
          id: 'serial-input',
          type: 'text',
          value: serialData,
          onChange: (event) => setSerialData(event.target.value),
          placeholder: '1, 2, 3, ...',
          autoFocus: true,
          disabled: isSubmitting,
        }),
        React.createElement(
          'button',
          {type: 'submit', disabled: isSubmitting || !serialData.trim()},
          isSubmitting ? 'Sending...' : 'Send'
        )
      )
    ),
    message && React.createElement('p', {className: 'status success'}, message),
    error && React.createElement('p', {className: 'status error'}, error)
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  React.createElement(SerialConsole)
);