# SecureHealthCare: A Zero Trust Security Framework for Healthcare Systems

**Problem Addressed**

Healthcare systems face escalating cybersecurity threats as they grow increasingly reliant on electronic health records, IoT medical devices, and cloud infrastructure. Traditional perimeter-based security models operate on an implicit trust assumption — treating everything inside the network as safe — a model that is fundamentally inadequate against ransomware, insider threats, and lateral movement attacks. Breaches in this sector go beyond data loss; they risk complete hospital shutdowns and direct patient harm. This project proposes SecureHealthCare, a Zero Trust Architecture (ZTA) built on the principle of "never trust, always verify," integrating Identity and Access Management (IAM), Software-Defined Perimeter (SDP), and Endpoint Detection and Response (EDR) into a unified, adaptive defense system tailored for healthcare environments.

**System Architecture**

SecureHealthCare is structured around two tightly coupled phases. Phase I — the Identity and Access Control Plane — handles continuous authentication via TOTP-based Multi-Factor Authentication, stateless JWT authorization using HMAC-SHA256, and policy-driven access enforcement through an API Gateway, SDP Controller, and SPA Controller. Sensitive patient data is encrypted at rest using AES-256-GCM. Phase II — the Data Control Plane — executes real-time endpoint monitoring through EDR agents deployed across hospital workstations and IoT devices, funneling structured telemetry into a centralized collector. Threats are identified through a hybrid detection engine combining hardcoded rule-based signatures (exfiltration, ransomware, brute-force, role violations) with a Random Forest ML model trained on the CSE-CIC-IDS2018 dataset. The entire system was containerized using Docker Compose across isolated bridge networks, enforcing microsegmentation with a strict default-deny communication model.

**Detection and Response**

The rule engine evaluates centralized telemetry against healthcare-specific threat signatures and classifies events by severity. In parallel, the ML engine processes telemetry as feature vectors and flags anomalies. Alerts are routed to an automated Response Controller that applies severity-proportionate enforcement: HIGH alerts trigger token revocation and access restriction, while CRITICAL alerts result in full segment isolation and IP blocking. All enforcement actions are persisted with host identity, trigger reason, and timestamp, and support auditable rollback via revert-isolation records.

**Results**

The Random Forest model, trained on 279,059 samples across 35 engineered features, achieved an attack recall of 95.27% and a ROC-AUC of 0.9872 at an optimized decision threshold of 0.14. SDP access control correctly enforced role-based allow/deny decisions, MFA gating was validated end-to-end through token issuance logs, and dynamic segment isolation was confirmed through audit trails showing backend-clinical-segment entering and exiting protected states. Runtime observability was provided through a Prometheus and Grafana stack monitoring five network segments, with 370 telemetry events recorded during validation.

**Future Work**

Planned extensions include dynamic per-user risk scoring based on behavioral signals, HIPAA-aligned structured audit reporting, automated recovery workflows post-containment, lightweight EDR agent deployment on embedded IoMT devices, and SHAP-based explainability for ML anomaly detections to support forensic review and operator trust.
