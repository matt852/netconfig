$(document).ready(function() {
  var events = $('#events');
  var table = $('#tblViewHosts').DataTable({
    "pageLength": 10,
    "lengthMenu": [
      [10, 25, 50, 100, -1],
      [10, 25, 50, 100, "All"]
    ],
    columnDefs: [{
      orderable: false,
      className: 'select-checkbox',
      targets: 0
    }],
    select: {
      style: 'multi',
      selector: 'td:first-child'
    }
  });
  tableSettings = table.settings(); //store its settings in oSettings

  $('#tblViewHosts tbody').on('click', 'td:first-child', function() {
    $(this).toggleClass('selected');
  });

});