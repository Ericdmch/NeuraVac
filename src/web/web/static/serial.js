const coolDownTime = 0;
let lastSubmitTime = 0;

async function submitSerial(serialData) {
  if (Date.now() - lastSubmitTime > coolDownTime) {
    
    const response = await fetch('/submit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(
        {data: serialData}
      )
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || 'Unable to submit serial data');
    } else{
      document.getElementById('serial-input').value = '';
      lastSubmitTime = Date.now();
    }

    return result.message;

  }
}

function handleSerialKeydown(event) {
  if (event.key === 'Enter') {
    submitSerial(event.target.value);
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const serialInput = document.getElementById('serial-input');
  if (serialInput) {
    serialInput.addEventListener('keydown', handleSerialKeydown);
  }
});