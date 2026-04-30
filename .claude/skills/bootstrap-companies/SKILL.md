---
name: bootstrap-companies
description: Populate config/companies.yaml with 30+ India-based and remote-friendly tech companies that hire DevOps / SRE / Cloud / Platform Engineers, mapped to their ATS platform. Use when starting the project or expanding the watchlist.
allowed-tools: Read Edit Write Bash WebSearch
---

# Bootstrap Companies Skill

## Goal
Produce a `config/companies.yaml` mapping companies to their ATS slug.

## Format
```yaml
greenhouse:
  - razorpay
  - postman
  - cred
lever:
  - swiggy
  - zomato
ashby:
  - linear
workday:
  - { company: visa, host: visa.wd1.myworkdayjobs.com, board: VisaCareers }
custom:
  - { name: zoho, url: https://careers.zohocorp.com/ }
```

## Step 1 — India-first targets (always include)
Razorpay, CRED, Postman, Atlassian-India, Swiggy, Zomato, Flipkart, Meesho, Zerodha, Groww, ShareChat, Hasura, Freshworks, Zoho, BrowserStack, PhonePe, Plivo, Dream11, Games24x7, Setu, Juspay, Chargebee, Locus, Hotstar, Sprinklr.

## Step 2 — Remote-friendly global (DevOps roles often open to India)
GitLab, HashiCorp, Cloudflare, Twilio, MongoDB, Elastic, Vercel, Netlify, Render, Fly.io, Datadog, Grafana Labs, Replit, Supabase.

## Step 3 — Resolve each to an ATS
For each company, web_search "<company> careers greenhouse OR lever OR ashby OR workday" and identify the platform. Patterns:
- `boards.greenhouse.io/<slug>` -> greenhouse
- `jobs.lever.co/<slug>` -> lever
- `jobs.ashbyhq.com/<slug>` -> ashby
- `*.myworkdayjobs.com/<board>` -> workday

## Step 4 — Validate each entry
Curl the JSON endpoint and confirm 200 OK before adding. Skip any that fail.

## Step 5 — Write companies.yaml
Group by ATS. Include a `last_validated` date comment at the top.

## Step 6 — Report
Tell the user: total count, breakdown by ATS, and any companies that couldn't be resolved.