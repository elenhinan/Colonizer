async function cfu_load_model() {
   let model_url = "/static/hive/model/model.json"
   model = await tf.loadGraphModel(model_url);
   // run first with zeros so everything is ready, reducing lag the first time
   let primer = tf.zeros([1,640,640,3], dtype='int32');
   await model.executeAsync(primer);
   console.log('CFU-detect - initialized');
};

async function cfu_detect() {
   let start = Date.now()

   let img_element = document.getElementById('image');
   let img_orig = tf.browser.fromPixels(img_element);
   let img_resized = tf.image.resizeBilinear(img_orig,[640,640]);
   let input_tensor = tf.cast(img_resized, dtype='int32').expandDims() ;
   let output_tensor = await model.executeAsync(input_tensor);

   let n = output_tensor[2].arraySync()[0]
   
   // clear overlay
   cfu_clear();

   cfu_arr = [];
   for (let i=0;i<n;i++) {
      let cfu = {
         cert : +output_tensor[3].arraySync()[0][i].toFixed(2), // + to convert from string to number again
         bbox : output_tensor[4].arraySync()[0][i].map(item => +item.toFixed(4)),
         label : labels[Number(output_tensor[5].arraySync()[0][i])],
         id: i,
         override : false
      }
      // skip if below threshold1
      if (cfu.cert < threshold_low) { break; }
      if (cfu.cert < threshold_high && !show_low) { continue; }
      // if not add to array and draw rectangles and labels
      cfu_arr.push(cfu);
   }
   // sort by size so largest is drawn first, so mouse over works as intended
   cfu_sorted = cfu_arr.slice().sort(cfu_compare);
   for (let i=0;i<cfu_sorted.length;i++) {
      cfu_add(cfu_sorted[i]);
   }

   let end = Date.now()
   console.log(`Execution time ${end-start} ms`);

   cfu_update_counts();
}


function cfu_compare(a,b) {
   a_size = (a.bbox[2] - a.bbox[0]) * (a.bbox[1] - a.bbox[3])
   b_size = (a.bbox[2] - a.bbox[0]) * (a.bbox[1] - a.bbox[3])
   
   if (a_size < b_size) {
      return -1;
   }
   if (a_size > b_size) {
      return 1;
   }
   return 0;
}

// load ML-model, and enable button to trigger it
$(document).ready(function() {
   cfu_load_model().then(function() {
      $('#detect').click(cfu_detect).prop('disabled', false);
   })
});
