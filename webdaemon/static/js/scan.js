// initialize on load
const image_placeholder = "/static/settleplate.svg"
const image_norefresh = "/images/live?norefresh"
const image_capture = "/images/live?crop=ring&light=ring"
$(document).ready(init_page);
$("#clear").click(init_page);

// zoom in on image on click
$("#image").click(function () {
   if ($(this).attr("src") == image_capture) {
      $("#imagemodal").modal('show');
   }
});
// when new image loaded, update imagezoom
$("#image").on('load', function() {
   if ($(this).attr("src") == image_capture) {
      $("#imagezoom").attr("src", image_norefresh);
   }
})

// refresh image on button click
$("#refresh").click(function () {
   $("#image").attr("src", image_capture);
   $("#counts").focus();
   $("#counts").attr("readonly", false);
});

//$("#image").load(function () {
//});

$("#counts").change(function () {
   $("#refresh").attr("disabled", true);
   $("#commit").attr("disabled", false);
   $("#commit").focus();
});

// commit image to db on click
$("#commit").click(function () {
   $("#commit").attr("disabled", true);
   $("#counts").attr('readonly', true);
   $("#commit").blur();
   $("#commit_wait").slideDown();
   $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/scan_add",
      data: JSON.stringify({ barcode: $("#barcode").val(), counts: $("#counts").val() }),
      success: function (data) {
         console.log(data);
         $("#commit_wait").slideUp();
         if (data.committed == true) {
            $("#commit_fail").slideUp();
            $("#commit_ok").html(`<strong>Success!</strong> Image commitd to DB`)
            $("#commit_ok").slideDown();
            table_append(data.ID, data.dT, data.Counts);
            setTimeout(init_page, 3000);
         } else {
            $("#commit_ok").slideUp();
            $("#commit_fail").slideDown();
         }
         slideup_all();
      },
      dataType: "json"
   });
   
});

function slideup_all() {
   setTimeout(function () {
      $("#commit_ok").slideUp();
      $("#commit_fail").slideUp();
   }, 3000);
}

// script for capturing barcode reader input on screen
// prevent submit on enter press
$("#barcode").change(function (event) {
   $("#barcode").attr('readonly', true);
   decode_text($("#barcode").val());
});

function decode_text(text_input) {
   console.log("Request barcode decode: " + text_input);
   $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/parse",
      data: JSON.stringify(text_input),
      success: function (data) {
         console.log(data);
         if ("serial" in data) {
            $("#barcode").val(data.serial)
            $("#image").attr("src", "/static/settleplate.svg") // reset image on new serial
            plate_info();
         }
      },
      dataType: "json"
   });
}

function plate_info() {
   //$("#loading").modal('show')
   $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/db/plate_info",
      data: JSON.stringify({ 'barcode': $("#barcode").val() }),
      success: function (data) {
         console.log(data);
         if ("error" in data) {
            $("#barcode").val("") // reset value in barcode and set focus
            alert(data.error);
            init_page();
         } else {
            $("#refresh").attr("disabled", false);
            $("#refresh").focus();
            $("#batch").val(data.Batch);
            $("#location").val(data.Location);
            $("#table_timepoints").empty();
            for (var i = 0; i < data.Timepoints.length; i++) {
               table_append(data.Timepoints[i].ID, data.Timepoints[i].dT, data.Timepoints[i].Counts);
            }
         }
         //$("#loading").modal('hide')
      },
      dataType: "json"
   });
}

function table_append(ID, dT, Counts) {
   $("#table_timepoints").append(`
      <tr>
         <td><a href="settleplate?id=${ID}" target="_blank">${ID}</a></td>
         <td>${dT}</td>
         <td>${Counts}</td>
      </tr>
   `);
}

function init_page() {
   $("#counts").val("");
   $("#counts").attr('readonly', true);
   $("#barcode").val("");
   $("#barcode").attr('readonly', false);
   $("#batch").val("");
   $("#location").val("");
   $("#table_timepoints").empty();
   $("#image").attr("src", image_placeholder);
   $("#imagezoom").attr("src", image_placeholder);
   $("#barcode").focus();
   $("#refresh").attr("disabled", true);
   $("#commit").attr("disabled", true);
   slideup_all();
}
