function cfu_toggle(id) {
   let element = document.getElementById(id);
   element.classList.toggle('CFU-positive');
   cfu_update_counts();
}

function cfu_add(cfu) {
   const radius = 0.2;
   let [ymin,xmin,ymax,xmax] = cfu.bbox;
   let width = xmax-xmin;
   let height = ymax-ymin;
   let rect = $(document.createElementNS("http://www.w3.org/2000/svg", "rect"));
   let text = $(document.createElementNS("http://www.w3.org/2000/svg", "text"));
   let group = $(document.createElementNS("http://www.w3.org/2000/svg", "g"));

   rect.attr({
      x: xmin,
      y: ymin,
      width: width.toFixed(4),
      height: height.toFixed(4),
      rx: (Math.min(width,height)*radius).toFixed(4)
   });

   text.attr({
      x: (xmin+xmax)/2,
      y: (ymin+ymax)/2
   });
   text.text(`${(cfu.cert*100).toFixed(0)}%`);

   group.addClass("CFU");
   group.attr('id', `CFU-${cfu.id}`);
   group.click(function() { cfu_toggle(this.id); });
   group.append(rect);
   group.append(text);
   if (cfu.cert >= threshold_high) (
      group.addClass('CFU-positive')
   )

   overlay.append(group)
}

function cfu_update_counts() {

   let n_cfus = $('.CFU-positive').length
   $("#counts").val(n_cfus);
}

function cfu_export() {
   let cfu_json = []
   $('.CFU-positive').each(function() {
      index = Number($(this)[0].id.split('-')[1]);
      cfu_json.push(cfu_arr[index]);
   })
   return JSON.stringify(cfu_json);
}

function cfu_import(jsondata) {
   cfu_arr = JSON.parse(jsondata);
   overlay.empty();
   cfu_arr.forEach(cfu => {
      cfu_add(cfu);
   });
   cfu_update_counts();
}

let cfu_arr;
var results;
var model;
var show_low = true;
var threshold_low = 0.20;
var threshold_high = 0.35
var overlay = $('#overlay');
const labels = ['Unused', 'CFU', 'MultiCFU', 'Bubble', 'Dish']
$('#counts').val(0);