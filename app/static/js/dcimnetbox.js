$(document).ready(function() {
  var events = $('#events');
  var table = $('#tblDCIMNetbox').DataTable({
    "pageLength": 10,
    "lengthMenu": [
      [10, 25, 50, 100, -1],
      [10, 25, 50, 100, "All"]
    ]
  });
});
