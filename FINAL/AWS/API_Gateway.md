# Amazon API Gateway — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon API Gateway?

**Answer:** API Gateway is a managed front door for HTTP APIs. It authenticates callers, throttles them, validates or transforms requests, and forwards the call to Lambda, an HTTP backend, or another AWS service. You do not run the gateway process yourself. It is regional (plus edge-optimized and private options) and sits in front of your code, not inside it.

---

#### 2. What is the difference between HTTP APIs and REST APIs?

**Answer:**

| | HTTP API | REST API |
| --- | --- | --- |
| Cost and latency | Lower cost, lower latency | Higher |
| Features | JWT authorizers, Lambda and HTTP proxy, CORS, stages | Usage plans, API keys, request validation, mapping templates, WAF, resource policies, private APIs |
| When | Most new Lambda or HTTP backends | You need API keys, usage plans, private VPC-only APIs, or body mapping |

Start with an **HTTP API** unless you need a REST-only feature. Do not confuse either of them with a REST style in your URL design. The names are product names.

---

#### 3. What is a stage?

**Answer:** A stage is a named deployment of the API, such as `dev` or `prod`, with its own URL, throttling, logs, and stage variables. A change to the API is not live until you **deploy** it to a stage (REST APIs). HTTP APIs auto-deploy if you turn that on. Point clients at the stage URL, or put a custom domain in front so the stage name is not part of the public URL.

---

#### 4. What backends can a route integrate with?

**Answer:**

* **Lambda proxy:** the raw HTTP request is the event. Your function returns status, headers, and body.
* **Lambda custom (REST):** mapping templates reshape the request and response. More control, more to maintain.
* **HTTP proxy:** any reachable URL, including an internal ALB.
* **AWS service:** REST APIs can call AWS APIs directly (for example DynamoDB) with a mapping template and an execution role.
* **Mock:** a fixed response, useful for a contract before the backend exists.

---

#### 5. What is proxy integration, and why is it the usual Lambda setup?

**Answer:** With `AWS_PROXY` or HTTP proxy, API Gateway passes the request through and expects a standard status/body response. You do not maintain Velocity templates for every field. The Lambda receives `requestContext`, headers, path parameters, and the body as a string. You parse JSON yourself. Use custom mapping only when the backend cannot be changed and the shapes do not match.

---

#### 6. How is API Gateway different from an ALB in front of Lambda or ECS?

**Answer:** An ALB routes HTTP and can target Lambda, but it does not give you usage plans, API keys, request validators, or JWT authorizers as built-in features. API Gateway is the better public API edge when you need those. An ALB is the better fit when the same hostname already routes to ECS and EC2, or when you want private HTTP inside the VPC without paying per million API Gateway requests. Many systems use API Gateway at the edge and an internal ALB behind it.

---

## Auth, throttling, and validation

#### 7. What authentication options do you have?

**Answer:**

* **JWT authorizer** (HTTP API): validates a JWT from Cognito or any OIDC issuer. Good default for user tokens.
* **Lambda authorizer** (token or request): your function returns an IAM policy. Use it for custom schemes.
* **IAM auth:** the caller signs the request with SigV4. Use it for service-to-service, not for browsers.
* **Cognito user pools** authorizer on REST APIs.
* **API keys** with usage plans: identification and quotas, **not** a secret you should treat as strong authentication.

None of these replace authorization inside the service (which user can see which order). The gateway only decides whether the call is allowed to reach the integration.

---

#### 8. Why are API keys not authentication?

**Answer:** API keys are a shared string, often sent in a header, and they identify a usage plan (rate and quota). They leak in logs, browser apps, and tickets. Use them to throttle a partner channel. Use JWT, IAM, or mTLS to prove identity. A public SPA cannot keep an API key secret.

---

#### 9. What is a usage plan?

**Answer:** A REST API object that ties API keys to throttle and quota limits (requests per second and requests per day or month). Different partners get different plans. HTTP APIs do not have usage plans. If you need partner quotas, you are looking at REST APIs or at a limit you enforce in the application.

---

#### 10. What are throttling limits, and what does the client see?

**Answer:** API Gateway has account-level and stage-level rate limits, plus per-route and per-usage-plan limits. When a caller exceeds them, the gateway returns **429 Too Many Requests** and does not invoke Lambda. Set a method throttle so one noisy client cannot consume the whole stage. The client should back off. This is separate from Lambda reserved concurrency, which returns a different error once the gateway has already decided to invoke.

---

#### 11. How do you validate a request body?

**Answer:** On REST APIs, attach a **JSON Schema** request model and turn on request validation for body, query, and headers. Invalid calls fail at the gateway with 400 and never reach Lambda. HTTP APIs do not offer the same validator. You validate in the function, or you put a REST API in front. Validation at the edge saves Lambda cost and gives clients a consistent error.

---

#### 12. What is a Lambda authorizer cache?

**Answer:** API Gateway can cache the authorizer result for a TTL, keyed by the token or by specified headers. That cuts latency and Lambda cost. If you cache too broadly, one user’s allow decision can be reused for another user. Key the cache on the authorization header. Keep the TTL short if permissions change often. A denied token should not be cached for long if you are locking accounts out.

---

## Networking and operations

#### 13. What is a private API?

**Answer:** A REST API that is reachable only through a **VPC interface endpoint** (`execute-api`), not from the public internet. Resource policies restrict which VPCs and accounts can call it. Use it for internal APIs that still want API Gateway features. HTTP APIs are not private in the same way. An internal ALB is the alternative when you do not need gateway features.

---

#### 14. How does API Gateway reach a private ALB or a private IP?

**Answer:** Create a **VPC Link**. REST APIs use a VPC link backed by an NLB. HTTP APIs can use a VPC link that reaches an ALB, an NLB, or a Cloud Map service directly. The integration URI is the private listener. Without a VPC link, “HTTP proxy” means a public URL. Private subnets are not magically reachable from the gateway’s managed fleet.

---

#### 15. What is the integration timeout, and why does it bite Lambda users?

**Answer:** REST and HTTP API integrations time out at **29 seconds**. A Lambda that runs for 40 seconds will be cut off at the gateway even though Lambda’s own timeout is 15 minutes. The client sees a 504. Long work belongs on a queue: the API stores the job, returns 202, and the client polls or gets a callback. Do not raise hopes that a setting will allow a two-minute synchronous HTTP call. It will not.

---

#### 16. What payload limits matter?

**Answer:** The maximum payload is **10 MB**. Lambda synchronous payloads are smaller in practice when you pass large binary bodies around (the Lambda invoke payload limit is 6 MB synchronous). Do not upload files through API Gateway. Use a presigned S3 URL. Base64 binary handling on REST APIs adds size overhead. Document the limit so clients fail clearly.

---

#### 17. How do custom domains and TLS work?

**Answer:** Request an ACM certificate in the same region as a regional API (or in us-east-1 for edge-optimized). Create a custom domain in API Gateway and a Route 53 alias to the domain target. Map `api.example.com` to a stage. Clients never see the `execute-api` hostname. TLS terminates at API Gateway. You choose a security policy for the TLS version.

---

#### 18. What is the difference between regional and edge-optimized endpoints?

**Answer:** **Regional** serves from the API’s region. You can put your own CloudFront distribution in front if you want a CDN. **Edge-optimized** is API Gateway’s built-in CloudFront distribution, aimed at globally distributed clients calling a REST API. For most backends in one region, regional plus CloudFront only if you need it is easier to reason about (caching, WAF, and headers you control).

---

#### 19. How do you turn on logs and find a failed request?

**Answer:** Enable **execution logs** and **access logs** to CloudWatch. Access logs should include the request id, route, status, integration latency, and authorizer latency. A client error you can debug has the `x-amzn-requestid` or `apigw-requestid` header. Execution logs are verbose. Leave them at INFO or ERROR in production and raise them while debugging. Also watch `5XXError`, `4XXError`, `Latency`, and `IntegrationLatency` metrics.

---

#### 20. What is a stage variable?

**Answer:** A key-value pair on a stage, such as a function name suffix or a backend URL. Integrations can reference it so the same API definition points at different Lambdas in `dev` and `prod`. Do not store secrets in stage variables. They are visible to anyone who can read the API config. Use Secrets Manager inside the backend.

---

#### 21. How do CORS errors happen even when the Lambda returns the right headers?

**Answer:** Browsers send an **OPTIONS** preflight. If no route handles OPTIONS, or the gateway does not have CORS configured, the browser fails before your GET runs. Configure CORS on the HTTP API or add an OPTIONS method. Gateway-generated errors (401, 429, 500 from the authorizer) also need CORS headers, or the browser hides them. A curl call succeeding and the browser failing is the usual symptom.

---

#### 22. What is a mapping template?

**Answer:** A REST API Velocity (VTL) script that turns a request into the integration payload and the integration response into an HTTP response. Use it for AWS service integrations and for legacy SOAP or XML backends. For Lambda, proxy integration removes the need. Templates are easy to break and hard to test. Keep them small or avoid them.

---

## Scenarios

#### 23. The API returns 500 and Lambda never logs a request. Where did it fail?

**Answer:** Before the integration: authorizer error, request validation, a bad mapping template, or IAM so the gateway cannot invoke the function. Check execution logs and whether the Lambda resource policy allows `apigateway.amazonaws.com` to invoke it. A 502 is more often a bad Lambda response shape (missing `statusCode`, body not a string). A 504 is the 29-second integration timeout or a Lambda crash the gateway could not parse.

---

#### 24. Lambda is throttled, but API Gateway throttling is not. What does the client see, and what do you change?

**Answer:** The gateway tries to invoke and Lambda returns a throttle. The client typically sees **429** or **502** depending on the integration. Fix it by raising reserved concurrency or the account limit, and by setting gateway throttling **lower** than what Lambda can accept so the overflow fails fast at the edge with a clear 429. A queue in front of bursty work is the other fix.

---

#### 25. You need to move an existing public REST API from EC2 onto Lambda without changing the URL.

**Answer:** Create a custom domain for the current hostname, map it to the stage, and cut Route 53 from the ALB to the API Gateway domain target when the routes match. Or put API Gateway behind the existing ALB only if you have a reason. Test the response shape, status codes, and CORS before the cut. Keep the ALB path ready as a rollback DNS change.

---

#### 26. Partner traffic must be limited to 10 requests per second, and user traffic to 50, on the same API. How?

**Answer:** On a REST API, two usage plans with different throttle rates, and API keys issued to the partners. User traffic uses JWT and a stage or method throttle, not the partner key. HTTP APIs can throttle per route and per stage but not with usage plans. If you are on HTTP APIs and you need partner quotas, enforce the quota in a Lambda authorizer plus a counter in DynamoDB, or use a REST API.

---

#### 27. A POST works in integration tests and fails from the browser with a CORS error. What do you add?

**Answer:** CORS configuration that allows the page’s origin, the `POST` method, and the headers the browser sends (`content-type`, `authorization`). Handle OPTIONS. Confirm error responses from the authorizer also return CORS headers. Do not use `Access-Control-Allow-Origin: *` together with credentials. Reflect the specific origin if the client sends cookies or authorization.

---

#### 28. How do you deploy API Gateway changes through CI without clicking the console?

**Answer:** Define the API in **SAM, CDK, CloudFormation, or OpenAPI** imported into the gateway. The pipeline deploys the stack and creates a deployment to the stage. For REST APIs, a change that is not deployed to the stage is a common “it works in the console editor but not in prod” bug. HTTP APIs with auto-deploy avoid that step. Keep stage variables and throttles in the same template.

---

#### 29. How would you design an endpoint that starts a 3-minute report?

**Answer:** `POST /reports` writes a job row and sends a message to SQS or starts a Step Functions execution, then returns **202** with a job id. `GET /reports/{id}` returns status. The API integration stays well under 29 seconds. The worker runs on Lambda (if it finishes in 15 minutes), ECS, or a state machine. The client polls or subscribes to a notification when the job completes.

---

#### 30. What would you monitor on a production API Gateway stage?

**Answer:** Count, 4xx, 5xx, latency, and integration latency, plus the Lambda function’s errors, throttles, and duration. Alarm on 5xx rate and on integration latency near 29 seconds. Access logs give you the route and request id. If you use a usage plan, watch throttle counts so a partner hitting the cap is a metric and not a surprise ticket. Trace one request with X-Ray when gateway latency and Lambda duration disagree.

---
