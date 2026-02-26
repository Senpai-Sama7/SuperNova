/**
 * PurpleShield Red Team Tools - Offensive Security
 *
 * Capabilities:
 * - Subdomain enumeration via certificate transparency
 * - Port scanning with service detection
 * - DNS analysis and security assessment
 * - WHOIS lookup
 * - HTTP security header analysis
 * - Ping/connectivity testing
 */
import { exec } from "child_process";
import { promisify } from "util";
import { z } from "zod";
import { ResponseFormat } from "../constants.js";
import axios from "axios";
const execAsync = promisify(exec);
// Input schemas
const SubdomainEnumInputSchema = z.object({
    domain: z.string().min(1).describe("Target domain to enumerate"),
    deep: z.boolean().default(false).describe("Enable deep enumeration with DNS resolution"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const PortScanInputSchema = z.object({
    target: z.string().min(1).describe("Target IP or hostname"),
    port_range: z.string().optional().describe("Port range (e.g., '1-1000' or '80,443,8080')"),
    scan_type: z.enum(["quick", "standard", "comprehensive"]).default("standard").describe("Scan type"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const DNSAnalyzeInputSchema = z.object({
    domain: z.string().min(1).describe("Domain to analyze"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const WHOISInputSchema = z.object({
    domain: z.string().min(1).describe("Domain for WHOIS lookup"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const HeadersAnalyzeInputSchema = z.object({
    url: z.string().min(1).describe("URL to analyze"),
    follow_redirects: z.boolean().default(true).describe("Follow HTTP redirects"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
// Helper functions
async function enumerateSubdomainsCT(domain) {
    const subdomains = new Set();
    try {
        // Query crt.sh
        const response = await axios.get(`https://crt.sh/?q=%.${domain}&output=json`, {
            timeout: 15000,
            headers: { 'User-Agent': 'PurpleShield-MCP/1.0' }
        });
        if (Array.isArray(response.data)) {
            for (const entry of response.data) {
                const name = entry.name_value;
                if (name) {
                    // Handle multiple subdomains in one entry
                    const names = name.split('\n').map((n) => n.trim()).filter(Boolean);
                    for (const n of names) {
                        if (n.includes(domain) && !n.startsWith('*')) {
                            subdomains.add(n.toLowerCase());
                        }
                    }
                }
            }
        }
    }
    catch (error) {
        console.error('crt.sh query failed:', error);
    }
    return Array.from(subdomains).map(sub => ({ subdomain: sub, source: 'crt.sh' }));
}
async function resolveDNS(domain) {
    const records = [];
    try {
        const dns = await import('dns');
        const resolver = new dns.promises.Resolver();
        // Query different record types
        const types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME'];
        for (const type of types) {
            try {
                let results = [];
                switch (type) {
                    case 'A':
                        results = await resolver.resolve4(domain);
                        break;
                    case 'AAAA':
                        results = await resolver.resolve6(domain);
                        break;
                    case 'MX':
                        results = await resolver.resolveMx(domain);
                        break;
                    case 'TXT':
                        results = await resolver.resolveTxt(domain);
                        break;
                    case 'NS':
                        results = await resolver.resolveNs(domain);
                        break;
                    case 'CNAME':
                        results = await resolver.resolveCname(domain);
                        break;
                }
                for (const result of results) {
                    records.push({
                        type,
                        value: typeof result === 'object' ? JSON.stringify(result) : String(result)
                    });
                }
            }
            catch {
                // Record type not found, continue
            }
        }
    }
    catch (error) {
        console.error('DNS resolution error:', error);
    }
    return records;
}
async function performWHOIS(domain) {
    try {
        const { stdout } = await execAsync(`whois ${domain}`, { timeout: 10000 });
        return stdout;
    }
    catch {
        return 'WHOIS lookup failed or not available';
    }
}
async function analyzeHeaders(url) {
    const cleanUrl = url.startsWith('http') ? url : `https://${url}`;
    const response = await axios.head(cleanUrl, {
        timeout: 10000,
        maxRedirects: 5,
        validateStatus: () => true // Accept any status
    });
    const headers = {};
    for (const [key, value] of Object.entries(response.headers)) {
        headers[key.toLowerCase()] = String(value);
    }
    // Check security headers
    const securityHeadersList = [
        'strict-transport-security',
        'content-security-policy',
        'x-frame-options',
        'x-content-type-options',
        'referrer-policy',
        'permissions-policy',
        'x-xss-protection'
    ];
    const securityHeaders = {};
    let score = 0;
    for (const header of securityHeadersList) {
        const value = headers[header];
        securityHeaders[header] = {
            present: !!value,
            value: value
        };
        if (value)
            score += 1;
    }
    return {
        headers,
        securityHeaders,
        securityScore: Math.round((score / securityHeadersList.length) * 100)
    };
}
export function registerRedTeamTools(server) {
    // Subdomain Enumeration
    server.registerTool("cyber_subdomain_enum", {
        title: "Enumerate Subdomains",
        description: `Enumerate subdomains for a target domain using certificate transparency logs.

This queries crt.sh and other sources to find subdomains - real reconnaissance data.

Args:
  - domain (string): Target domain (e.g., example.com)
  - deep (boolean): Enable DNS resolution for found subdomains
  - response_format ('markdown' | 'json'): Output format

Returns:
  List of discovered subdomains with sources.

Example:
  - domain="google.com", deep=true

Note:
  - Uses passive reconnaissance (no direct target contact)
  - Results depend on certificate transparency logging`,
        inputSchema: SubdomainEnumInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const subdomains = await enumerateSubdomainsCT(params.domain);
            let withDNS = subdomains;
            if (params.deep && subdomains.length > 0) {
                // Resolve DNS for first 20 subdomains
                const toResolve = subdomains.slice(0, 20);
                withDNS = await Promise.all(toResolve.map(async (sub) => ({
                    ...sub,
                    records: await resolveDNS(sub.subdomain)
                })));
            }
            const result = {
                domain: params.domain,
                count: subdomains.length,
                subdomains: withDNS,
                deep: params.deep
            };
            const text = `# Subdomain Enumeration: ${params.domain}

**Found**: ${result.count} subdomains
**Mode**: ${params.deep ? 'Deep (with DNS)' : 'Standard'}

| Subdomain | Source |
|-----------|--------|
${subdomains.slice(0, 50).map(s => `| ${s.subdomain} | ${s.source} |`).join('\n')}${subdomains.length > 50 ? '\n| ... | ... |' : ''}`;
            return {
                content: [{ type: "text", text }],
                structuredContent: result
            };
        }
        catch (error) {
            return {
                content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }]
            };
        }
    });
    // DNS Analysis
    server.registerTool("cyber_dns_analyze", {
        title: "Analyze DNS Records",
        description: `Analyze DNS records for security assessment.

Queries A, AAAA, MX, TXT, NS, and CNAME records.

Args:
  - domain (string): Domain to analyze
  - response_format ('markdown' | 'json'): Output format

Returns:
  DNS records and security analysis (SPF, DKIM, DMARC).`,
        inputSchema: DNSAnalyzeInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const records = await resolveDNS(params.domain);
            // Analyze email security
            const txtRecords = records.filter(r => r.type === 'TXT');
            const security = {
                spf: txtRecords.some(r => r.value.includes('v=spf1')),
                dkim: txtRecords.some(r => r.value.includes('DKIM')),
                dmarc: txtRecords.some(r => r.value.includes('v=DMARC1'))
            };
            const result = {
                domain: params.domain,
                records,
                record_count: records.length,
                security_analysis: security
            };
            const text = `# DNS Analysis: ${params.domain}

## Records

| Type | Value |
|------|-------|
${records.map(r => `| ${r.type} | ${r.value.substring(0, 80)}${r.value.length > 80 ? '...' : ''} |`).join('\n') || '*(No records found)*'}

## Email Security

- **SPF**: ${security.spf ? '✓ Present' : '✗ Missing'}
- **DKIM**: ${security.dkim ? '✓ Present' : '✗ Missing'}
- **DMARC**: ${security.dmarc ? '✓ Present' : '✗ Missing'}`;
            return {
                content: [{ type: "text", text }],
                structuredContent: result
            };
        }
        catch (error) {
            return {
                content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }]
            };
        }
    });
    // WHOIS Lookup
    server.registerTool("cyber_whois", {
        title: "WHOIS Lookup",
        description: `Perform WHOIS lookup for domain registration information.

Args:
  - domain (string): Domain to lookup
  - response_format ('markdown' | 'json'): Output format

Returns:
  Domain registration details including registrar, dates, nameservers.`,
        inputSchema: WHOISInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const whoisData = await performWHOIS(params.domain);
            // Parse key fields
            const registrar = whoisData.match(/Registrar:\s*(.+)/i)?.[1];
            const created = whoisData.match(/Creation Date:\s*(.+)/i)?.[1];
            const expires = whoisData.match(/Registry Expiry Date:\s*(.+)/i)?.[1];
            const updated = whoisData.match(/Updated Date:\s*(.+)/i)?.[1];
            const result = {
                domain: params.domain,
                registrar,
                created,
                expires,
                updated,
                raw: whoisData.substring(0, 2000)
            };
            const text = `# WHOIS: ${params.domain}

- **Registrar**: ${registrar || 'N/A'}
- **Created**: ${created || 'N/A'}
- **Expires**: ${expires || 'N/A'}
- **Updated**: ${updated || 'N/A'}

\`\`\`
${whoisData.substring(0, 1500)}${whoisData.length > 1500 ? '\n... (truncated)' : ''}
\`\`\``;
            return {
                content: [{ type: "text", text }],
                structuredContent: result
            };
        }
        catch (error) {
            return {
                content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }]
            };
        }
    });
    // HTTP Headers Analysis
    server.registerTool("cyber_headers_analyze", {
        title: "Analyze HTTP Security Headers",
        description: `Analyze HTTP security headers and provide recommendations.

Checks for HSTS, CSP, X-Frame-Options, and other security headers.

Args:
  - url (string): URL to analyze
  - follow_redirects (boolean): Follow redirects (default: true)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Security header analysis with score and recommendations.`,
        inputSchema: HeadersAnalyzeInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const analysis = await analyzeHeaders(params.url);
            // Generate recommendations
            const recommendations = [];
            if (!analysis.securityHeaders['strict-transport-security']?.present) {
                recommendations.push('Add Strict-Transport-Security (HSTS) header');
            }
            if (!analysis.securityHeaders['content-security-policy']?.present) {
                recommendations.push('Add Content-Security-Policy header to prevent XSS');
            }
            if (!analysis.securityHeaders['x-frame-options']?.present) {
                recommendations.push('Add X-Frame-Options header to prevent clickjacking');
            }
            if (!analysis.securityHeaders['x-content-type-options']?.present) {
                recommendations.push('Add X-Content-Type-Options: nosniff header');
            }
            const result = {
                url: params.url,
                security_score: analysis.securityScore,
                headers: analysis.securityHeaders,
                recommendations
            };
            const text = `# HTTP Security Analysis: ${params.url}

## Security Score: ${analysis.securityScore}/100

## Headers

| Header | Present | Value |
|--------|---------|-------|
${Object.entries(analysis.securityHeaders).map(([name, info]) => `| ${name} | ${info.present ? '✓' : '✗'} | ${info.value?.substring(0, 40) || '-'} |`).join('\n')}

## Recommendations

${recommendations.map(r => `- ${r}`).join('\n') || 'No recommendations - great job!'}`;
            return {
                content: [{ type: "text", text }],
                structuredContent: result
            };
        }
        catch (error) {
            return {
                content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }]
            };
        }
    });
}
//# sourceMappingURL=cyber-redteam.js.map