import http from 'k6/http';
import { sleep } from 'k6';

// with some package not simple k6 when command line with dashboard, can see the menitor on http://127.0.0.1:5665
// example command  k6 run --out dashboard script.js
// this k6 which is recreated by xk6 path is at home/dcnlab/go/bin 
export const options = {
  vus: 1, 
  duration: "500s", // Test duration (adjust as needed)
};

const url = "http://192.168.72.11:5500/simplerequest"; // Replace with your server URL

const body = {
  // Define your POST request body data here
  // e.g., { name: "John", age: 30 }
  name: "John", 
  age: 30
};

const jsonData = JSON.stringify(body);

export default function test() {
  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };
  http.post(url, jsonData, params);
  sleep(1);
}



