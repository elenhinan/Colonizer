$(document).ready(function() {
   $("#generate").on("click", function() {
      // setup search params
      params = [
         "period="+$("#period").val(),
         "number="+$("#number").val(),
         "year="+$("#year").val()
      ];
      // reload page with new search
      window.location.href =
           window.location.pathname +
          '?' + params.join('&');
   });
   $("#period").on("change", update_selector);
   update_selector();
})

function update_selector() {
   var selection_max = Number($("#period").val());
   $("#number option").remove(); // remove old
   for (let i=1; i <= selection_max; i++) {
      $("#number").append(new Option(i,i));
   }
}

function settleplate_modal(spID) {
   $('#imagezoom').attr("src", ""); // set image to none first to prevent flicker of prev image
   $('#imagezoom').attr("src", "/images/"+spID); // load iamge
   $('#imagemodal').modal('show'); // show modal
   return false;
}