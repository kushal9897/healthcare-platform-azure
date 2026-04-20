/**
 * k6 Load Test - Healthcare Platform
 * Tests API performance under realistic healthcare workload patterns.
 *
 * Usage:
 *   k6 run --env BASE_URL=https://api.healthcare.com tests/load/healthcare-load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// --- Custom Metrics ----------------------------------------------------------

const patientCreated = new Counter('patients_created');
const assessmentRequested = new Counter('assessments_requested');
const errorRate = new Rate('errors');
const patientLatency = new Trend('patient_api_latency', true);
const assessmentLatency = new Trend('assessment_api_latency', true);

// --- Test Configuration ------------------------------------------------------

export const options = {
  scenarios: {
    // Simulate normal business hours traffic
    normal_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },   // Ramp up
        { duration: '5m', target: 20 },   // Steady state
        { duration: '2m', target: 50 },   // Peak hours
        { duration: '5m', target: 50 },   // Sustained peak
        { duration: '2m', target: 20 },   // Cool down
        { duration: '1m', target: 0 },    // Ramp down
      ],
      gracefulRampDown: '30s',
    },

    // Spike test - sudden burst (e.g., mass screening event)
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      startTime: '20m',
      stages: [
        { duration: '10s', target: 100 },  // Sudden spike
        { duration: '1m', target: 100 },   // Hold spike
        { duration: '10s', target: 0 },    // Drop
      ],
    },
  },

  thresholds: {
    // SLO: 99% of requests < 500ms
    http_req_duration: ['p(99)<500', 'p(95)<200'],
    // SLO: Error rate < 0.1%
    errors: ['rate<0.001'],
    // Custom thresholds
    patient_api_latency: ['p(95)<300'],
    assessment_api_latency: ['p(95)<2000'],
    // Checks must pass > 99%
    checks: ['rate>0.99'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// --- Helper Functions --------------------------------------------------------

function randomPatient() {
  const names = ['John', 'Jane', 'Alice', 'Bob', 'Carlos', 'Diana', 'Ethan', 'Fiona'];
  const surnames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller'];
  const genders = ['male', 'female', 'other'];

  return {
    given_name: names[Math.floor(Math.random() * names.length)],
    family_name: surnames[Math.floor(Math.random() * surnames.length)],
    birth_date: `${1950 + Math.floor(Math.random() * 50)}-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`,
    gender: genders[Math.floor(Math.random() * genders.length)],
    phone: `+1${Math.floor(Math.random() * 9000000000 + 1000000000)}`,
  };
}

// --- Test Scenarios ----------------------------------------------------------

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  group('Health Checks', function () {
    const res = http.get(`${BASE_URL}/health`);
    check(res, {
      'health status is 200': (r) => r.status === 200,
      'health response is healthy': (r) => r.json().status === 'healthy',
    });
    errorRate.add(res.status !== 200);
  });

  group('Patient Operations', function () {
    // Create patient
    const patient = randomPatient();
    const createRes = http.post(`${BASE_URL}/patients`, JSON.stringify(patient), { headers });

    check(createRes, {
      'patient created (201)': (r) => r.status === 201,
      'patient has ID': (r) => r.json().id !== undefined,
    });

    patientLatency.add(createRes.timings.duration);
    errorRate.add(createRes.status !== 201);

    if (createRes.status === 201) {
      patientCreated.add(1);
      const patientId = createRes.json().id;

      // Read patient
      const getRes = http.get(`${BASE_URL}/patients/${patientId}`);
      check(getRes, {
        'get patient (200)': (r) => r.status === 200,
      });
      patientLatency.add(getRes.timings.duration);

      // Search patients
      const searchRes = http.get(`${BASE_URL}/patients?name=${patient.given_name}`);
      check(searchRes, {
        'search patients (200)': (r) => r.status === 200,
        'search has results': (r) => r.json().total > 0,
      });
      patientLatency.add(searchRes.timings.duration);
    }
  });

  group('Clinical Assessments', function () {
    const assessmentTypes = ['primary_care', 'cardiology', 'pharmacy', 'emergency', 'nursing'];
    const assessmentType = assessmentTypes[Math.floor(Math.random() * assessmentTypes.length)];

    const assessReq = {
      patient_id: 'test-patient-001',
      assessment_type: assessmentType,
      chief_complaint: 'Patient presents with persistent headache for 3 days, moderate severity, no trauma history.',
      vitals: {
        blood_pressure: '120/80',
        heart_rate: 72,
        temperature: 98.6,
        respiratory_rate: 16,
      },
    };

    const res = http.post(`${BASE_URL.replace(':8000', ':8001')}/assess`, JSON.stringify(assessReq), { headers });

    check(res, {
      'assessment created (201)': (r) => r.status === 201,
      'assessment completed': (r) => r.json().status === 'completed',
      'has recommendations': (r) => r.json().recommendations && r.json().recommendations.length > 0,
    });

    assessmentLatency.add(res.timings.duration);
    errorRate.add(res.status !== 201);

    if (res.status === 201) {
      assessmentRequested.add(1);
    }
  });

  sleep(Math.random() * 2 + 1); // 1-3 second think time
}

// --- Teardown Summary --------------------------------------------------------

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'load-test-results.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data) {
  return `
=== Healthcare Platform Load Test Summary ===
Patients created:      ${data.metrics.patients_created ? data.metrics.patients_created.values.count : 0}
Assessments requested: ${data.metrics.assessments_requested ? data.metrics.assessments_requested.values.count : 0}
Error rate:            ${data.metrics.errors ? (data.metrics.errors.values.rate * 100).toFixed(3) : 0}%
P95 latency:           ${data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'].toFixed(0) : 0}ms
P99 latency:           ${data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'].toFixed(0) : 0}ms
`;
}
