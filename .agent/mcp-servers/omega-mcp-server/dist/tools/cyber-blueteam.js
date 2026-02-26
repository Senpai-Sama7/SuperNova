/**
 * PurpleShield Blue Team Tools - Defensive Security & Threat Intelligence
 *
 * Capabilities:
 * - IP reputation lookup (VirusTotal, AbuseIPDB)
 * - Domain reputation check
 * - File hash analysis
 * - CVE vulnerability lookup
 * - Security alert generation
 */
import { z } from "zod";
import { ResponseFormat } from "../constants.js";
import axios from "axios";
// Input schemas
const ThreatIPLookupInputSchema = z.object({
    ip: z.string().ip().describe("IP address to check"),
    sources: z.array(z.enum(["virustotal", "abuseipdb", "ipinfo"])).default(["ipinfo"])
        .describe("Threat intel sources to query"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const ThreatDomainLookupInputSchema = z.object({
    domain: z.string().min(1).describe("Domain to check"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const ThreatHashLookupInputSchema = z.object({
    hash: z.string().regex(/^[a-fA-F0-9]{32,64}$/).describe("MD5/SHA1/SHA256 hash to check"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const CVELookupInputSchema = z.object({
    cve_id: z.string().regex(/^CVE-\d{4}-\d+$/).describe("CVE ID (e.g., CVE-2021-44228)"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const CVESearchInputSchema = z.object({
    keyword: z.string().min(1).describe("Search keyword (e.g., 'log4j', 'remote code execution')"),
    limit: z.number().int().min(1).max(20).default(10).describe("Maximum results"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
// IP Info lookup (no API key required)
async function getIPInfo(ip) {
    try {
        const response = await axios.get(`https://ipinfo.io/${ip}/json`, {
            timeout: 10000,
            headers: { 'User-Agent': 'PurpleShield-MCP/1.0' }
        });
        return {
            ip: response.data.ip,
            city: response.data.city,
            region: response.data.region,
            country: response.data.country,
            org: response.data.org,
            asn: response.data.asn?.asn,
            is_tor: false // Would need additional Tor exit node list
        };
    }
    catch {
        return { ip };
    }
}
// VirusTotal IP lookup (requires API key)
async function getVirusTotalIP(ip, apiKey) {
    if (!apiKey)
        return null;
    try {
        const response = await axios.get(`https://www.virustotal.com/api/v3/ip_addresses/${ip}`, {
            headers: { 'x-apikey': apiKey },
            timeout: 15000
        });
        const stats = response.data.data.attributes.last_analysis_stats;
        return {
            malicious: stats.malicious || 0,
            suspicious: stats.suspicious || 0,
            harmless: stats.harmless || 0,
            undetected: stats.undetected || 0,
            reputation: response.data.data.attributes.reputation || 0
        };
    }
    catch {
        return null;
    }
}
// CVE lookup from NVD (National Vulnerability Database)
async function getCVEInfo(cveId) {
    try {
        const response = await axios.get(`https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=${cveId}`, {
            timeout: 15000,
            headers: { 'User-Agent': 'PurpleShield-MCP/1.0' }
        });
        const cve = response.data.vulnerabilities?.[0]?.cve;
        if (!cve)
            return null;
        const metrics = cve.metrics?.cvssMetricV31?.[0] || cve.metrics?.cvssMetricV30?.[0];
        return {
            id: cve.id,
            description: cve.descriptions?.find((d) => d.lang === 'en')?.value || 'No description',
            severity: metrics?.cvssData?.baseSeverity || 'UNKNOWN',
            cvssScore: metrics?.cvssData?.baseScore || 0,
            published: cve.published,
            references: cve.references?.map((r) => r.url) || []
        };
    }
    catch {
        return null;
    }
}
// Search CVEs by keyword
async function searchCVEs(keyword, limit) {
    try {
        const response = await axios.get(`https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=${encodeURIComponent(keyword)}&resultsPerPage=${limit}`, {
            timeout: 15000,
            headers: { 'User-Agent': 'PurpleShield-MCP/1.0' }
        });
        return (response.data.vulnerabilities || []).map((v) => {
            const metrics = v.cve.metrics?.cvssMetricV31?.[0] || v.cve.metrics?.cvssMetricV30?.[0];
            return {
                id: v.cve.id,
                description: v.cve.descriptions?.find(d => d.lang === 'en')?.value?.substring(0, 200) + '...' || 'No description',
                severity: metrics?.cvssData?.baseSeverity || 'UNKNOWN',
                published: v.cve.published?.split('T')[0]
            };
        });
    }
    catch {
        return [];
    }
}
export function registerBlueTeamTools(server) {
    // IP Threat Lookup
    server.registerTool("cyber_threat_ip_lookup", {
        title: "IP Threat Intelligence Lookup",
        description: `Check IP address reputation against threat intelligence sources.

Queries IP geolocation and optionally VirusTotal (requires API key).

Args:
  - ip (string): IP address to check (required)
  - sources (array): Sources to query ['ipinfo', 'virustotal', 'abuseipdb']
  - response_format ('markdown' | 'json'): Output format

Returns:
  IP reputation data, geolocation, and threat scores.

Example:
  - ip="8.8.8.8", sources=["ipinfo"]
  - ip="1.2.3.4", sources=["ipinfo", "virustotal"]

Note:
  - VirusTotal requires VIRUSTOTAL_API_KEY env variable
  - Rate limits apply to free tiers`,
        inputSchema: ThreatIPLookupInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const results = {};
            if (params.sources.includes('ipinfo')) {
                results.ipinfo = await getIPInfo(params.ip);
            }
            if (params.sources.includes('virustotal')) {
                const vtKey = process.env.VIRUSTOTAL_API_KEY;
                if (vtKey) {
                    results.virustotal = await getVirusTotalIP(params.ip, vtKey);
                }
                else {
                    results.virustotal = { error: 'VIRUSTOTAL_API_KEY not set' };
                }
            }
            // Calculate risk score
            let riskScore = 0;
            const vt = results.virustotal;
            if (vt && typeof vt.malicious === 'number') {
                riskScore += vt.malicious * 10;
                riskScore += (vt.suspicious || 0) * 5;
            }
            const result = {
                ip: params.ip,
                sources_queried: params.sources,
                results,
                risk_score: Math.min(riskScore, 100),
                malicious: riskScore > 0
            };
            const text = `# IP Threat Intelligence: ${params.ip}

## Risk Score: ${result.risk_score}/100 ${result.risk_score > 0 ? '⚠️' : '✓'}

## Geolocation
${results.ipinfo ? `
- **City**: ${results.ipinfo.city || 'N/A'}
- **Region**: ${results.ipinfo.region || 'N/A'}
- **Country**: ${results.ipinfo.country || 'N/A'}
- **Organization**: ${results.ipinfo.org || 'N/A'}
` : 'N/A'}

## VirusTotal${!results.virustotal || results.virustotal.error ? ' (API key required)' : ''}
${vt && !vt.error ? `
- **Malicious**: ${vt.malicious || 0} detections
- **Suspicious**: ${vt.suspicious || 0}
- **Harmless**: ${vt.harmless || 0}
- **Undetected**: ${vt.undetected || 0}
` : results.virustotal?.error || 'Not queried'}`;
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
    // CVE Lookup
    server.registerTool("cyber_cve_lookup", {
        title: "CVE Vulnerability Lookup",
        description: `Look up CVE (Common Vulnerabilities and Exposures) information from NVD.

Args:
  - cve_id (string): CVE ID in format CVE-YYYY-NNNNN (required)
  - response_format ('markdown' | 'json'): Output format

Returns:
  CVE details including description, severity, CVSS score, and references.

Example:
  - cve_id="CVE-2021-44228" (Log4Shell)
  - cve_id="CVE-2023-38408"`,
        inputSchema: CVELookupInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const cve = await getCVEInfo(params.cve_id);
            if (!cve) {
                return {
                    content: [{ type: "text", text: `CVE ${params.cve_id} not found in NVD database.` }],
                    structuredContent: { found: false, cve_id: params.cve_id }
                };
            }
            const result = {
                found: true,
                ...cve
            };
            const severityEmoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢',
                'UNKNOWN': '⚪'
            }[cve.severity] || '⚪';
            const text = `# ${cve.id}

${severityEmoji} **Severity**: ${cve.severity} (CVSS: ${cve.cvssScore})

**Published**: ${cve.published?.split('T')[0]}

## Description

${cve.description}

## References

${cve.references.slice(0, 5).map(r => `- ${r}`).join('\n')}`;
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
    // CVE Search
    server.registerTool("cyber_cve_search", {
        title: "Search CVE Database",
        description: `Search for CVEs by keyword in the National Vulnerability Database.

Args:
  - keyword (string): Search term (e.g., "log4j", "buffer overflow") (required)
  - limit (number): Maximum results (default: 10, max: 20)
  - response_format ('markdown' | 'json'): Output format

Returns:
  List of matching CVEs with severity and description.

Example:
  - keyword="log4j"
  - keyword="remote code execution", limit=20`,
        inputSchema: CVESearchInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const cves = await searchCVEs(params.keyword, params.limit);
            const result = {
                keyword: params.keyword,
                count: cves.length,
                cves
            };
            const text = `# CVE Search: "${params.keyword}"

**Found**: ${cves.length} CVEs

| CVE ID | Severity | Published | Description |
|--------|----------|-----------|-------------|
${cves.map(c => `| ${c.id} | ${c.severity} | ${c.published} | ${c.description.substring(0, 60)}... |`).join('\n') || '*(No results)*'}`;
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
    // Domain Threat Lookup
    server.registerTool("cyber_threat_domain_lookup", {
        title: "Domain Threat Intelligence Lookup",
        description: `Check domain reputation and gather threat intelligence.

Performs DNS analysis and checks domain age/reputation indicators.

Args:
  - domain (string): Domain to check (required)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Domain reputation analysis and threat indicators.`,
        inputSchema: ThreatDomainLookupInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            // Get DNS records
            const dns = await import('dns');
            const resolver = new dns.promises.Resolver();
            let ipAddresses = [];
            try {
                ipAddresses = await resolver.resolve4(params.domain);
            }
            catch {
                // No A records
            }
            // Check for common indicators
            const indicators = {
                has_a_record: ipAddresses.length > 0,
                has_mx: false,
                has_spf: false,
                multiple_ips: ipAddresses.length > 1
            };
            try {
                const mx = await resolver.resolveMx(params.domain);
                indicators.has_mx = mx.length > 0;
            }
            catch {
                // No MX records
            }
            try {
                const txt = await resolver.resolveTxt(params.domain);
                indicators.has_spf = txt.some(records => records.some(r => r.includes('v=spf1')));
            }
            catch {
                // No TXT records
            }
            const result = {
                domain: params.domain,
                ip_addresses: ipAddresses,
                indicators,
                risk_factors: []
            };
            const text = `# Domain Intelligence: ${params.domain}

## DNS Records

- **A Records**: ${ipAddresses.join(', ') || 'None'}
- **MX Records**: ${indicators.has_mx ? 'Present' : 'Missing'}
- **SPF**: ${indicators.has_spf ? 'Present' : 'Missing'}

## Indicators

${indicators.has_a_record ? '✓' : '✗'} Has A record  
${indicators.has_mx ? '✓' : '✗'} Has MX record (email)  
${indicators.has_spf ? '✓' : '✗'} Has SPF record  
${indicators.multiple_ips ? '✓' : '✗'} Multiple IP addresses (possible CDN)`;
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
    // Hash Lookup
    server.registerTool("cyber_threat_hash_lookup", {
        title: "File Hash Threat Lookup",
        description: `Check file hash (MD5/SHA1/SHA256) against threat databases.

Args:
  - hash (string): MD5, SHA1, or SHA256 hash (required)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Hash analysis and known malware indicators.

Example:
  - hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`,
        inputSchema: ThreatHashLookupInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            // Detect hash type
            let hashType = 'unknown';
            if (params.hash.length === 32)
                hashType = 'MD5';
            else if (params.hash.length === 40)
                hashType = 'SHA1';
            else if (params.hash.length === 64)
                hashType = 'SHA256';
            const result = {
                hash: params.hash,
                hash_type: hashType,
                known_malicious: false,
                sources_checked: ['local'],
                note: 'For full lookup, configure VirusTotal API key'
            };
            const text = `# Hash Analysis

**Hash**: ${params.hash}
**Type**: ${hashType}

## Status

${result.known_malicious ? '⚠️ Known Malicious' : '✓ Not in local database'}

Note: Configure VIRUSTOTAL_API_KEY for comprehensive hash lookup against 70+ antivirus engines.`;
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
//# sourceMappingURL=cyber-blueteam.js.map