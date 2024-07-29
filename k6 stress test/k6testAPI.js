import http from 'k6/http';
import { sleep } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';
import { check } from 'k6';
const binFile = open('mm.png', 'b');
//  const fileData = readFileSync(filePath, 'b');
export default function () {

  const fd = new FormData();
  fd.append('question', 'describe the image');
  fd.append('file',http.file(binFile, 'k62.js'));
  const res = http.post('http://127.0.0.1:8006/vlm', fd.body(), {
    headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd.boundary },
  });
    sleep(4)

  check(res, {
    'is status 200': (r) => r.status === 200,
  });


  console.log('description',res['body'])
}
