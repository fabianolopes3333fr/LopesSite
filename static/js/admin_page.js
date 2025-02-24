function toggleScheduledFor(status) {
  var scheduledForField = document
    .getElementById('id_scheduled_for')
    .closest('.form-row');
  if (status === 'scheduled') {
    scheduledForField.style.display = 'block';
  } else {
    scheduledForField.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  var statusField = document.getElementById('id_status');
  toggleScheduledFor(statusField.value);
});
