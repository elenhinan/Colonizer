$(document).ready(function() {
   $("#search").on("click", function() {
      // setup search params
      params = [
         "from="+$("#date_from").val(),
         "to="+$("#date_to").val(),
         "batch="+$("#batch").val(),
         "name="+$("#name").val()
      ];
      // reload page with new search
      window.location.href =
           window.location.pathname +
          '?' + params.join('&');
   });
})

function isoDate(dateobj) {
   var options = { year: 'numeric', month: '2-digit', day: '2-digit'};
   var isodate = dateobj.toLocaleDateString(undefined, options).replaceAll('/','-');
   return isodate;
}