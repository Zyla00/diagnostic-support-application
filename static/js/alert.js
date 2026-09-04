const notyf = new Notyf({
  duration: 4000,
  position: { x: 'right', y: 'top' },
  types: [
    {
      type: 'success',
      background: 'green',
      icon: false
    },
    {
      type: 'error',
      background: 'red',
      icon: false
    },
    {
      type: 'info',
      background: 'blue',
      icon: false
    }
  ]
});

function showToast(message, type = 'info') {
  notyf.open({
    type: type === 'success' || type === 'error' ? type : 'info',
    message
  });
}
