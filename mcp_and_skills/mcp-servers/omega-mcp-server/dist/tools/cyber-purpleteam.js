/**
 * PurpleShield Purple Team Tools - MITRE ATT&CK & Exercise Management
 *
 * Capabilities:
 * - MITRE ATT&CK technique lookup
 * - Detection coverage mapping
 * - Purple team exercise creation/management
 */
import { z } from "zod";
import { ResponseFormat } from "../constants.js";
// MITRE ATT&CK Techniques Database (subset of common techniques)
const MITRE_TECHNIQUES = {
    'T1566': {
        id: 'T1566',
        name: 'Phishing',
        description: 'Adversaries may send phishing messages to gain access to victim systems.',
        tactics: ['Initial Access'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor for suspicious email patterns, URL analysis, attachment inspection'
    },
    'T1059': {
        id: 'T1059',
        name: 'Command and Scripting Interpreter',
        description: 'Adversaries may abuse command and script interpreters to execute commands.',
        tactics: ['Execution'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor process creation, command-line logging, script execution'
    },
    'T1053': {
        id: 'T1053',
        name: 'Scheduled Task/Job',
        description: 'Adversaries may abuse task scheduling functionality to facilitate initial or recurring execution.',
        tactics: ['Execution', 'Persistence', 'Privilege Escalation'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor task creation events, scheduled job modifications'
    },
    'T1071': {
        id: 'T1071',
        name: 'Application Layer Protocol',
        description: 'Adversaries may communicate using OSI application layer protocols to avoid detection.',
        tactics: ['Command and Control'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor network traffic for unusual patterns, DNS anomalies'
    },
    'T1083': {
        id: 'T1083',
        name: 'File and Directory Discovery',
        description: 'Adversaries may enumerate files and directories or may search in specific locations.',
        tactics: ['Discovery'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor file system access patterns, command-line arguments'
    },
    'T1078': {
        id: 'T1078',
        name: 'Valid Accounts',
        description: 'Adversaries may obtain and abuse credentials of existing accounts.',
        tactics: ['Initial Access', 'Persistence', 'Privilege Escalation', 'Defense Evasion'],
        platforms: ['Windows', 'macOS', 'Linux', 'Network'],
        detection: 'Monitor for unusual login patterns, impossible travel, off-hours access'
    },
    'T1021': {
        id: 'T1021',
        name: 'Remote Services',
        description: 'Adversaries may use remote services to access and interact with compromised systems.',
        tactics: ['Lateral Movement'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor remote connection events, authentication logs'
    },
    'T1041': {
        id: 'T1041',
        name: 'Exfiltration Over C2 Channel',
        description: 'Adversaries may steal data by exfiltrating it over an existing C2 channel.',
        tactics: ['Exfiltration'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor network traffic volume, data transfer anomalies'
    },
    'T1003': {
        id: 'T1003',
        name: 'OS Credential Dumping',
        description: 'Adversaries may attempt to dump credentials to obtain account login and credential material.',
        tactics: ['Credential Access'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor LSASS access, SAM database access, credential manager access'
    },
    'T1486': {
        id: 'T1486',
        name: 'Data Encrypted for Impact',
        description: 'Adversaries may encrypt data on target systems to interrupt availability.',
        tactics: ['Impact'],
        platforms: ['Windows', 'macOS', 'Linux'],
        detection: 'Monitor for mass file modifications, unusual encryption activity'
    }
};
// Input schemas
const MITRELookupInputSchema = z.object({
    technique_id: z.string().regex(/^T\d{4}$/).describe("MITRE technique ID (e.g., T1566)"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const MITRESearchInputSchema = z.object({
    keyword: z.string().min(1).describe("Search keyword"),
    tactic: z.string().optional().describe("Filter by tactic"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const ExerciseCreateInputSchema = z.object({
    name: z.string().min(1).describe("Exercise name"),
    description: z.string().optional().describe("Exercise description"),
    techniques: z.array(z.string()).describe("MITRE technique IDs to test"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
const CoverageMapInputSchema = z.object({
    detected_techniques: z.array(z.string()).describe("Techniques you can detect"),
    response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN)
}).strict();
// In-memory exercise storage (would use database in production)
const exercises = new Map();
export function registerPurpleTeamTools(server) {
    // MITRE ATT&CK Technique Lookup
    server.registerTool("cyber_mitre_lookup", {
        title: "MITRE ATT&CK Technique Lookup",
        description: `Look up MITRE ATT&CK technique details.

Args:
  - technique_id (string): Technique ID (e.g., T1566, T1059) (required)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Technique details including description, tactics, platforms, and detection methods.

Example:
  - technique_id="T1566" (Phishing)
  - technique_id="T1059" (Command and Scripting Interpreter)`,
        inputSchema: MITRELookupInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const technique = MITRE_TECHNIQUES[params.technique_id];
            if (!technique) {
                return {
                    content: [{ type: "text", text: `Technique ${params.technique_id} not found in local database. Visit https://attack.mitre.org/ for full ATT&CK matrix.` }],
                    structuredContent: { found: false, id: params.technique_id }
                };
            }
            const result = {
                found: true,
                ...technique
            };
            const text = `# ${technique.id}: ${technique.name}

## Description

${technique.description}

## Tactics

${technique.tactics.map(t => `- ${t}`).join('\n')}

## Platforms

${technique.platforms.join(', ')}

## Detection

${technique.detection}

---

📚 [View on MITRE ATT&CK](https://attack.mitre.org/techniques/${technique.id}/)`;
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
    // MITRE ATT&CK Search
    server.registerTool("cyber_mitre_search", {
        title: "Search MITRE ATT&CK Techniques",
        description: `Search MITRE ATT&CK techniques by keyword.

Args:
  - keyword (string): Search term (required)
  - tactic (string): Filter by tactic (optional)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Matching techniques with descriptions.

Example:
  - keyword="phishing"
  - keyword="credential", tactic="Credential Access"`,
        inputSchema: MITRESearchInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: true
        }
    }, async (params) => {
        try {
            const keyword = params.keyword.toLowerCase();
            const matches = Object.values(MITRE_TECHNIQUES).filter(t => {
                const matchesKeyword = t.name.toLowerCase().includes(keyword) ||
                    t.description.toLowerCase().includes(keyword) ||
                    t.tactics.some(tactic => tactic.toLowerCase().includes(keyword));
                if (params.tactic) {
                    return matchesKeyword && t.tactics.some(t => t.toLowerCase().includes(params.tactic.toLowerCase()));
                }
                return matchesKeyword;
            });
            const result = {
                keyword: params.keyword,
                tactic_filter: params.tactic,
                count: matches.length,
                techniques: matches
            };
            const text = `# MITRE ATT&CK Search: "${params.keyword}"${params.tactic ? ` (Tactic: ${params.tactic})` : ''}

**Found**: ${matches.length} techniques

| ID | Name | Tactics |
|----|------|---------|
${matches.map(t => `| ${t.id} | ${t.name} | ${t.tactics.join(', ')} |`).join('\n') || '*(No matches)*'}`;
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
    // Create Purple Team Exercise
    server.registerTool("cyber_exercise_create", {
        title: "Create Purple Team Exercise",
        description: `Create a new purple team exercise to test detection capabilities.

Args:
  - name (string): Exercise name (required)
  - description (string): Exercise description (optional)
  - techniques (array): MITRE technique IDs to test (required)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Exercise ID and details.

Example:
  - name="Q1 Credential Access Test", techniques=["T1003", "T1078"]

Note:
  - Exercises are stored in memory (lost on restart)
  - Use techniques from cyber_mitre_search`,
        inputSchema: ExerciseCreateInputSchema,
        annotations: {
            readOnlyHint: false,
            destructiveHint: false,
            idempotentHint: false,
            openWorldHint: false
        }
    }, async (params) => {
        try {
            const id = `ex_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            const exercise = {
                id,
                name: params.name,
                description: params.description || '',
                techniques: params.techniques,
                status: 'planned',
                created: new Date().toISOString(),
                findings: []
            };
            exercises.set(id, exercise);
            // Validate techniques
            const validTechniques = params.techniques.filter(t => MITRE_TECHNIQUES[t]);
            const invalidTechniques = params.techniques.filter(t => !MITRE_TECHNIQUES[t]);
            const result = {
                exercise,
                valid_techniques: validTechniques.length,
                invalid_techniques: invalidTechniques,
                technique_details: validTechniques.map(t => ({
                    id: t,
                    name: MITRE_TECHNIQUES[t]?.name
                }))
            };
            const text = `# Purple Team Exercise Created

**ID**: ${id}
**Name**: ${params.name}
**Status**: Planned

## Techniques (${validTechniques.length})

${result.technique_details.map(t => `- ${t.id}: ${t.name}`).join('\n')}

${invalidTechniques.length > 0 ? `\n⚠️ Invalid technique IDs: ${invalidTechniques.join(', ')}` : ''}

## Next Steps

1. Review techniques with your team
2. Execute attack simulations
3. Document detection capabilities
4. Update findings with cyber_exercise_update`;
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
    // Detection Coverage Mapping
    server.registerTool("cyber_coverage_map", {
        title: "Map Detection Coverage",
        description: `Map your detection coverage against MITRE ATT&CK framework.

Shows which techniques you can detect and identifies gaps.

Args:
  - detected_techniques (array): List of technique IDs you can detect (required)
  - response_format ('markdown' | 'json'): Output format

Returns:
  Coverage percentage and gap analysis.

Example:
  - detected_techniques=["T1566", "T1059", "T1003"]

Note:
  - Compares against local technique database
  - Full ATT&CK matrix has 200+ techniques`,
        inputSchema: CoverageMapInputSchema,
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false
        }
    }, async (params) => {
        try {
            const allTechniques = Object.keys(MITRE_TECHNIQUES);
            const detected = params.detected_techniques.filter(t => MITRE_TECHNIQUES[t]);
            const undetected = allTechniques.filter(t => !detected.includes(t));
            const coverage = Math.round((detected.length / allTechniques.length) * 100);
            // Group by tactic
            const tacticCoverage = {};
            for (const [id, tech] of Object.entries(MITRE_TECHNIQUES)) {
                for (const tactic of tech.tactics) {
                    if (!tacticCoverage[tactic]) {
                        tacticCoverage[tactic] = { total: 0, detected: 0 };
                    }
                    tacticCoverage[tactic].total++;
                    if (detected.includes(id)) {
                        tacticCoverage[tactic].detected++;
                    }
                }
            }
            const result = {
                total_techniques: allTechniques.length,
                detected_count: detected.length,
                coverage_percent: coverage,
                detected,
                gaps: undetected,
                tactic_coverage: tacticCoverage
            };
            const text = `# Detection Coverage Map

## Overall Coverage: ${coverage}% (${detected.length}/${allTechniques.length})

## Coverage by Tactic

| Tactic | Detected | Total | Coverage |
|--------|----------|-------|----------|
${Object.entries(tacticCoverage).map(([tactic, stats]) => `| ${tactic} | ${stats.detected} | ${stats.total} | ${Math.round((stats.detected / stats.total) * 100)}% |`).join('\n')}

## Detected Techniques

${detected.map(t => `✓ ${t}: ${MITRE_TECHNIQUES[t]?.name}`).join('\n') || 'None'}

## Gaps (Undetected)

${undetected.slice(0, 10).map(t => `✗ ${t}: ${MITRE_TECHNIQUES[t]?.name}`).join('\n')}${undetected.length > 10 ? `\n... and ${undetected.length - 10} more` : ''}

---

💡 **Recommendation**: Focus on high-impact techniques in your top tactics first.`;
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
//# sourceMappingURL=cyber-purpleteam.js.map