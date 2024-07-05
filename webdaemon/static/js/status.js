$(document).ready(function() {
   update_status();
   setTimeout(update_status, 5000);
});

function update_status() {
   $.ajax({
      dataType: "json",
      url: "/status",
      success: function (data) {
         for (key in data) {
            icon = $(`#status_${key}`)
            if (data[key]) {
               icon.addClass("status-online")
               icon.removeClass("status-offline")               
            } else {
               icon.addClass("status-offline")
               icon.removeClass("status-online")
            }
         }
      }
   });
}