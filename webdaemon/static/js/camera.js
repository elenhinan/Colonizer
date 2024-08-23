$(document).ready(function() {
   $("#refresh").click(function () {
      //$("#image").attr("src", image_capture);
      fetch($("#image").attr("src"), {cache: 'reload', mode: 'no-cors'});
   });

   $("#save").click(function () {
      $("#save_wait").slideDown();
      $.ajax({
         type: "POST",
         contentType: "application/json; charset=utf-8",
         url: "/save_image",
         data: JSON.stringify({ batch: $("#batch").val() }),
         success: function (data) {
            console.log(data);
            $("#save_wait").slideUp();
            if (data.saved == true) {
               $("#save_fail").slideUp();
               $("#save_ok").html(`<strong>Success!</strong> Image saved to <i>${data.filename}</i>`)
               $("#save_ok").slideDown();
            } else {
               $("#save_ok").slideUp();
               $("#save_fail").slideDown();
            }
            slideup_all();
         },
         dataType: "json"
      });
   });
});

function slideup_all() {
   setTimeout(function () {
      $("#save_ok").slideUp();
      $("#save_fail").slideUp();
   }, 8000);
}