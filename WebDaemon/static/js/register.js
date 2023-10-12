var new_user;
var new_batch;
var new_serial;
var new_lotno;
var new_location;
var text_input;
var batch_locations;

const GLYPH = {
   WAIT: 'wait',
   PASS: 'pass',
   FAIL: 'fail'
}

const STATE = {
   RESET:    'reset',
   BATCH:    'batch',
   USER:     'user',
   SERIAL:   'serial',
   LOCATION: 'location',
   REGISTER: 'register',
   LOOP:     'loop'
}


// transition state machine
function transition(new_state) {
   console.log(`New state: ${new_state}`);
   switch(new_state) {
      default:
      case STATE.USER:
         new_user=null;
         new_batch=null;
         new_serial=null;
         new_lotno=null;
         new_location=null;
         text_input = "";
         $("#barcode").val(text_input);
         update_fields();
         update_table();
         $("#duplicate").slideUp();
         set_glyph($("#user_glyph"),GLYPH.ACTIVE);
         set_glyph($("#batch_glyph"),GLYPH.WAIT);
         set_glyph($("#lotno_glyph"),GLYPH.WAIT);
         set_glyph($("#location_glyph"),GLYPH.WAIT);
         set_glyph($("#input_glyph"),GLYPH.ACTIVE);
         state=STATE.USER;
         break;

      case STATE.BATCH:
         update_fields();
         set_glyph($("#user_glyph"),GLYPH.PASS);
         set_glyph($("#batch_glyph"),GLYPH.ACTIVE);
         state=STATE.BATCH;
         break;

      case STATE.LOOP:
         new_serial=null;
         new_lotno=null;
         new_location=null;
         set_glyph($("#location_glyph"),GLYPH.WAIT);

      case STATE.SERIAL:
         update_fields();
         update_table();
         set_glyph($("#batch_glyph"),GLYPH.PASS);
         set_glyph($("#lotno_glyph"),GLYPH.ACTIVE);
         state=STATE.SERIAL;
         break;

      case STATE.LOCATION:
         update_fields();
         set_glyph($("#lotno_glyph"),GLYPH.PASS);
         set_glyph($("#location_glyph"),GLYPH.ACTIVE);
         state=STATE.LOCATION;
         break;

      case STATE.REGISTER:
         set_glyph($("#location_glyph"),GLYPH.PASS);
         state=STATE.REGISTER;
         register_new();
         break;
   }
}

function process_input(data) {
   switch(state) {
      case STATE.USER:
         if("user" in data) {
            new_user = data.user;
            input_pass();
            transition(STATE.BATCH);
         } else {
            input_fail();
         }
         break;

      case STATE.BATCH:
         if("batch" in data) {
            new_batch = data.batch;
            input_pass();
            transition(STATE.SERIAL);
         } else {
            input_fail();
         }
         break;
      
      case STATE.SERIAL:
         if("serial" in data) {
            // check if settleplate already registered
            if(data.used > 0) {
               $("#duplicate-plate").slideDown();
               input_fail();
            } else {
               $("#duplicate-plate").slideUp();
               new_serial = data.serial;
               if("lot" in data) new_lotno = data.lot;
               else new_lotno = data.serial;
               input_pass();
               transition(STATE.LOCATION);
            }
         } else {
            input_fail();
         }
         break;

      case STATE.LOCATION:
         if("location" in data) {
            if (location_exist(data["location"])) {
               $("#duplicate-location").slideDown();
               input_fail();
            } else {
               $("#duplicate-location").slideUp();
               new_location = data.location;
               input_pass();
               transition(STATE.REGISTER);
            }
         } else {
            input_fail();
         }
         break;

      default:
         break;
   }
}

function input_pass() {
   set_glyph($("#input_glyph"),GLYPH.PASS);
   input_clear_timeout = setTimeout(function() {
      set_glyph($("#input_glyph"),GLYPH.ACTIVE);
      $("#barcode").val(null);
   }, 2000);
}

function input_fail() {
   set_glyph($("#input_glyph"),GLYPH.FAIL);
}

function set_glyph(glyph, state) {
   switch(state) {
      case GLYPH.WAIT:
         glyph.toggleClass('fa-question-circle', true);
         glyph.toggleClass('fa-check-circle', false);
         glyph.toggleClass('fa-exclamation-circle', false);
         glyph.css("color", "grey");
         break;
      case GLYPH.ACTIVE:
         glyph.toggleClass('fa-question-circle', true);
         glyph.toggleClass('fa-check-circle', false);
         glyph.toggleClass('fa-exclamation-circle', false);
         glyph.css("color", "blue");
         break;
      case GLYPH.PASS:
         glyph.toggleClass('fa-question-circle', false);
         glyph.toggleClass('fa-check-circle', true);
         glyph.toggleClass('fa-exclamation-circle', false);
         glyph.css("color", "green");
         break;
      case GLYPH.FAIL:
         glyph.toggleClass('fa-question-circle', false);
         glyph.toggleClass('fa-check-circle', false);
         glyph.toggleClass('fa-exclamation-circle', true);
         glyph.css("color", "red");
         break;
      default:
   }
}

function update_table() {
   $("#table_registered").empty();
   if(new_batch == null) return;
   $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/batch_bydate",
      data: JSON.stringify({'batch':new_batch}),
         success: function (data) {
            batch_locations = data;
            console.log(batch_locations);
            for(var i=0; i<batch_locations.length;i++) {
               $("#table_registered").append(`
                  <tr>
                     <td>${batch_locations[i].ScanDate}</td>
                     <td>${batch_locations[i].Barcode}</td>
                     <td>${batch_locations[i].Location}</td>
                  </tr>
               `)
            }
         },
      dataType: "json"
   });
}

function location_exist(location) {
   for(var i=0; i<batch_locations.length;i++) {
      if (location == batch_locations[i].Location)
         return true;
   }
   return false;
}

function update_fields() {
   $("#user").val(new_user);
   $("#lotno").val(new_lotno);
   $("#location").val(new_location);
   $("#batch").val(new_batch);
}

function register_new() {
   if(new_user != null && new_batch != null && new_serial != null && new_location != null) {
      $.ajax({
         type: "POST",
         contentType: "application/json; charset=utf-8",
         url: "/register_new",
         data: JSON.stringify({user:new_user, batch:new_batch, serial:new_serial, location:new_location}),
            success: function (data) {
               console.log(data);
               setTimeout(function() {
                  transition(STATE.LOOP);
               }, 1000);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) { 
                           alert("Status: " + textStatus); alert("Error: " + errorThrown);
            },
         dataType: "json"
      });
   }
}

function decode_text() {
   console.log("Request barcode decode: "+text_input);
   $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/parse",
      data: JSON.stringify(text_input),
         success: function (data) {
            console.log(data);
            process_input(data);
         },
      dataType: "json"
   });
}

$(document).ready(function() {
   
   $(document).keypress(function(event) {
      var k = event.which || event.keyCode;
      var c = String.fromCharCode(k);
      text_input = text_input + c;
      $("#barcode").val(text_input);
   });

   $(document).keydown(function(event) {
      if(event.keyCode == 13) {
         decode_text();
         text_input = "";
      }
   });
   // prevent submit on enter press
   $(window).keydown(function(event){
    if(event.keyCode == 13) {
       event.preventDefault();
       return false;
    }
   });
   transition(STATE.USER);
})