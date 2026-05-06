// Handles DataTables initialisation and infotext accessibility for Training page

$(document).ready(function() {
  var $sortTable = $("#sortTable");
  if ($sortTable.length && !$sortTable.hasClass('dataTable')) {
    $sortTable.DataTable({
      "paging": true,
      "pageLength": 5,
      "lengthMenu": [5, 10, 15, 20],
      "info": false,
      "searching": true,
    });
    $(".dataTables_length").addClass("bs-select");
  }
  // accessibility: show/hide description on mouse and keyboard focus
  $(".infotext").attr({
  // if target is already a button you don't need these attributes, but if it's not, add them to make it accessible
  //   tabindex: 0,
  //   role: "button",
    "aria-haspopup": "true",
    "aria-expanded": "false",
  });
  $sortTable.on("mouseenter focusin", ".infotext",function() {
    $(this).find(".description").show();
    $(this).attr("aria-expanded", "true");
  });
  $sortTable.on("mouseleave focusout", ".infotext",function() {
    $(this).find(".description").hide();
    $(this).attr("aria-expanded", "false");
  });

  $sortTable.on("draw.dt", function () {
    $(".description").hide();
    $(".infotext").attr("aria-expanded", "false");
  });
});
