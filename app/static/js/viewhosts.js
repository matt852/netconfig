$(document).ready(function() {
  var events = $('#events');
  var table = $('#tblViewHosts').DataTable({
    //dom: 'lBfrtip', // WIP for select all button
    "pageLength": 10,
    "lengthMenu": [
      [10, 25, 50, 100, -1],
      [10, 25, 50, 100, "All"]
    ], // Settings for entire table
    columnDefs: [{
      orderable: false,
      searchable: false,
      className: 'select-checkbox',
      targets: 0
    }, // First column - checkbox
    {
      visible: false,
      searchable: false,
      targets: 6
    }], // Hidden column at end for host id
    select: {
      style: 'multi',
      selector: 'td:first-child'
    },
    buttons: [
      'selectAll',
      'selectNone'
    ], // Buttons for table
    language: {
      buttons: {
        selectAll: "Select all devices",
        selectNone: "Select no devices"
      }
    } // Wording for buttons on table
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

  // Display tblViewHosts buttons // WIP for select all button
  //table.buttons().container()
  //    .appendTo( $('.col-sm-6:eq(0)', table.table().container() ) );
});