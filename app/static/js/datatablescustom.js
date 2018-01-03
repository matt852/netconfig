$(document).ready(function() {
  $('#tblViewHosts').DataTable({
    "pageLength": 10,
    "lengthMenu": [
      [10, 25, 50, 100, -1],
      [10, 25, 50, 100, "All"]
    ]
  });
});
