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
    },
    {
      visible: false,
      searchable: false,
      targets: 6
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

  $('#btnDeleteDevices').click(function(e) {
    // Get current table Length
    var tableLength = table.page.len();
    // Briefly redraw table with all pages, as the below function can only detect selected rows on visible pages
    table.page.len(-1).draw();

    var selectedDevices = [];
    var rows = $('tr.selected');
    var rowData = table.rows(rows).data();

    $.each($(rowData), function(key, value) {
      var tableData = table.row({
        selected: true
      }).data()[6];
      var div = document.createElement("div");
      div.innerHTML = this[6];
      selectedDevices.push(div.textContent || div.innerText || "");
    });
    table.page.len(tableLength).draw();

    var url = '/confirm/confirmmultiplehostdelete/'

    for (var i in selectedDevices) {
      url = url + '&' + selectedDevices[i];
    }

    // Loads next page on button click
    // Pass URL with an '&' in front of each device, in this format:
    // /confirm/confirmmultipleintenable/[host.id]/&int1&int2&int3...etc
    window.location.href = url;
  });

});

$('#modalLocalCredentials').on('show.bs.modal', function(event) {
  var button = $(event.relatedTarget) // Button that triggered the modal

  var hostname = button.data('hostname') // Extract info from data-* attributes
  var hostid = button.data('hostid') // Extract info from data-* attributes

  var modal = $(this)

  modal.find('.modal-title').text('Local credentials for ' + hostname)
  modal.find('.modal-result').load('/modallocalcredentials/' + hostid)
})

$('#modalLocalCredentials').on('hidden.bs.modal', function() {
  var modal = $(this)
  modal.find('.modal-title').text('')
  modal.find('.modal-result').text('')
})