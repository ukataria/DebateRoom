import { useEffect, useMemo, useRef } from "react";
import { Scale, Shield, Sword, Search, BookOpen } from "lucide-react";
import type { EvidenceItem, ToolCallEvent } from "../types";

interface JudgeSummaryProps {
  text: string;
  isActive: boolean;
  evidence: EvidenceItem[];
  toolCalls: ToolCallEvent[];
  onCitationClick: (evidenceId: string) => void;
}

interface ParsedJudgeSummary {
  overview: string;
  defenseHighlights: string[];
  prosecutionHighlights: string[];
  keyExchanges: string[];
  evidenceAssessment: string[];
  recommendation: string;
}

const SECTION_MARKERS = [
  { marker: "OVERVIEW:", key: "overview" },
  { marker: "DEFENSE HIGHLIGHTS:", key: "defenseHighlights" },
  { marker: "PROSECUTION HIGHLIGHTS:", key: "prosecutionHighlights" },
  { marker: "KEY EXCHANGES:", key: "keyExchanges" },
  { marker: "EVIDENCE ASSESSMENT:", key: "evidenceAssessment" },
  { marker: "RECOMMENDATION:", key: "recommendation" },
] as const;

function parseJudgeSummary(text: string): ParsedJudgeSummary {
  const result: ParsedJudgeSummary = {
    overview: "",
    defenseHighlights: [],
    prosecutionHighlights: [],
    keyExchanges: [],
    evidenceAssessment: [],
    recommendation: "",
  };

  const positions = SECTION_MARKERS.map((m) => ({
    ...m,
    index: text.indexOf(m.marker),
  }));

  for (let i = 0; i < positions.length; i++) {
    const pos = positions[i];
    if (pos.index === -1) continue;

    const contentStart = pos.index + pos.marker.length;
    const nextPos = positions
      .filter((p) => p.index > pos.index)
      .sort((a, b) => a.index - b.index)[0];
    const contentEnd = nextPos ? nextPos.index : text.length;
    const content = text.slice(contentStart, contentEnd).trim();

    if (pos.key === "overview" || pos.key === "recommendation") {
      result[pos.key] = content;
    } else {
      result[pos.key] = parseBullets(content);
    }
  }

  return result;
}

function parseBullets(content: string): string[] {
  return content
    .split(/\n-\s*/)
    .map((s) => s.replace(/^-\s*/, "").trim())
    .filter(Boolean);
}

type SourceEntry = { index: number; evidenceId: string };

export function JudgeSummary({
  text,
  isActive,
  evidence,
  toolCalls,
  onCitationClick,
}: JudgeSummaryProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const parsed = useMemo(() => parseJudgeSummary(text), [text]);

  const sourceMap = useMemo(() => {
    const map = new Map<string, SourceEntry>();
    for (let i = 0; i < evidence.length; i++) {
      map.set(evidence[i].id, {
        index: i + 1,
        evidenceId: evidence[i].id,
      });
    }
    for (const tc of toolCalls) {
      if (tc.result_id && !map.has(tc.result_id)) {
        const evMatch = evidence.find((ev) => ev.id === tc.result_id);
        if (evMatch) {
          const existing = map.get(evMatch.id);
          if (existing) map.set(tc.result_id, existing);
        }
      }
    }
    return map;
  }, [evidence, toolCalls]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [text]);

  const hasContent =
    parsed.overview ||
    parsed.defenseHighlights.length > 0 ||
    parsed.prosecutionHighlights.length > 0;

  return (
    <div
      ref={scrollRef}
      className="mx-auto w-full max-w-5xl px-6 py-8"
      style={{ animation: "fade-in 0.6s ease-out" }}
    >
      <div className="rounded-2xl border border-gold/30 bg-court-surface p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Scale className="h-7 w-7 text-gold" />
            <h2 className="text-xl font-bold text-court-text">
              Judge's Summary
            </h2>
            {isActive && (
              <span className="flex items-center gap-1 text-xs text-court-text-muted">
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full bg-gold"
                  style={{ animation: "typing-dot 1.4s infinite" }}
                />
                Analyzing...
              </span>
            )}
          </div>
        </div>

        {!hasContent && isActive && (
          <div className="py-8 text-center text-court-text-muted">
            The judge is reviewing the debate transcript...
          </div>
        )}

        <div className="space-y-5">
          {/* Overview */}
          {parsed.overview && (
            <div
              className="rounded-xl border border-court-border bg-court-panel p-4"
              style={{ animation: "fade-in 0.4s ease-out" }}
            >
              <p className="text-sm leading-relaxed text-court-text">
                <InlineText
                  text={parsed.overview}
                  sourceMap={sourceMap}
                  onCitationClick={onCitationClick}
                />
              </p>
            </div>
          )}

          {/* Defense + Prosecution Highlights — two columns */}
          {(parsed.defenseHighlights.length > 0 ||
            parsed.prosecutionHighlights.length > 0) && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Defense Highlights */}
              <HighlightSection
                title="Defense Highlights"
                icon={<Shield className="h-4 w-4 text-defense" />}
                items={parsed.defenseHighlights}
                accentBorder="border-defense/20"
                accentBg="bg-defense/5"
                sourceMap={sourceMap}
                onCitationClick={onCitationClick}
              />

              {/* Prosecution Highlights */}
              <HighlightSection
                title="Prosecution Highlights"
                icon={<Sword className="h-4 w-4 text-prosecution" />}
                items={parsed.prosecutionHighlights}
                accentBorder="border-prosecution/20"
                accentBg="bg-prosecution/5"
                sourceMap={sourceMap}
                onCitationClick={onCitationClick}
              />
            </div>
          )}

          {/* Key Exchanges */}
          {parsed.keyExchanges.length > 0 && (
            <BulletSection
              title="Key Exchanges"
              icon={<Search className="h-4 w-4 text-gold" />}
              items={parsed.keyExchanges}
              accentBorder="border-gold/20"
              accentBg="bg-gold/5"
              sourceMap={sourceMap}
              onCitationClick={onCitationClick}
            />
          )}

          {/* Evidence Assessment */}
          {parsed.evidenceAssessment.length > 0 && (
            <BulletSection
              title="Evidence Assessment"
              icon={<BookOpen className="h-4 w-4 text-evidence" />}
              items={parsed.evidenceAssessment}
              accentBorder="border-evidence/20"
              accentBg="bg-evidence/5"
              sourceMap={sourceMap}
              onCitationClick={onCitationClick}
            />
          )}

          {/* Recommendation */}
          {parsed.recommendation && (
            <div
              className="rounded-xl border border-gold/30 bg-gold/5 p-4"
              style={{ animation: "fade-in 0.4s ease-out" }}
            >
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gold">
                Recommendation
              </h3>
              <p className="text-sm font-medium leading-relaxed text-court-text">
                <InlineText
                  text={parsed.recommendation}
                  sourceMap={sourceMap}
                  onCitationClick={onCitationClick}
                />
              </p>
            </div>
          )}

          {isActive && (
            <span
              className="ml-0.5 inline-block h-4 w-0.5 bg-gold"
              style={{ animation: "typing-dot 1s infinite" }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function HighlightSection({
  title,
  icon,
  items,
  accentBorder,
  accentBg,
  sourceMap,
  onCitationClick,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
  accentBorder: string;
  accentBg: string;
  sourceMap: Map<string, SourceEntry>;
  onCitationClick: (evidenceId: string) => void;
}) {
  if (items.length === 0) return null;

  return (
    <div
      className={`rounded-xl border ${accentBorder} ${accentBg} p-4`}
      style={{ animation: "fade-in 0.4s ease-out" }}
    >
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h3 className="text-xs font-semibold uppercase tracking-wider text-court-text-muted">
          {title}
        </h3>
      </div>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li
            key={i}
            className="text-sm leading-relaxed text-court-text-dim"
            style={{
              animation: `fade-in 0.3s ease-out ${i * 0.1}s both`,
            }}
          >
            <InlineText
              text={item}
              sourceMap={sourceMap}
              onCitationClick={onCitationClick}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

function BulletSection({
  title,
  icon,
  items,
  accentBorder,
  accentBg,
  sourceMap,
  onCitationClick,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
  accentBorder: string;
  accentBg: string;
  sourceMap: Map<string, SourceEntry>;
  onCitationClick: (evidenceId: string) => void;
}) {
  return (
    <div
      className={`rounded-xl border ${accentBorder} ${accentBg} p-4`}
      style={{ animation: "fade-in 0.4s ease-out" }}
    >
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h3 className="text-xs font-semibold uppercase tracking-wider text-court-text-muted">
          {title}
        </h3>
      </div>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li
            key={i}
            className="text-sm leading-relaxed text-court-text-dim"
            style={{
              animation: `fade-in 0.3s ease-out ${i * 0.1}s both`,
            }}
          >
            <InlineText
              text={item}
              sourceMap={sourceMap}
              onCitationClick={onCitationClick}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

function InlineText({
  text,
  sourceMap,
  onCitationClick,
}: {
  text: string;
  sourceMap: Map<string, SourceEntry>;
  onCitationClick: (evidenceId: string) => void;
}) {
  const renderCitation = (id: string, key: string) => {
    const entry = sourceMap.get(id);
    if (!entry) return null;

    return (
      <button
        key={key}
        type="button"
        onClick={() => onCitationClick(entry.evidenceId)}
        className="inline cursor-pointer font-mono text-xs font-bold text-evidence transition-colors hover:text-evidence-dim"
        title="Jump to evidence"
      >
        [{entry.index}]
      </button>
    );
  };

  const parts = text.split(/(\[TOOL:[^\]]+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("[TOOL:")) {
          const id = part.slice(6, -1);
          return renderCitation(id, String(i));
        }
        const bareToolParts = part.split(
          /\[?(tool_[a-f0-9]{4,8})\]?/gi
        );
        if (bareToolParts.length > 1) {
          return bareToolParts.map((sub, j) => {
            if (/^tool_[a-f0-9]{4,8}$/i.test(sub)) {
              return renderCitation(sub, `${i}-${j}`);
            }
            return <span key={`${i}-${j}`}>{sub}</span>;
          });
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
