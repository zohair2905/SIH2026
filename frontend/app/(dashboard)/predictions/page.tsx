"use client";

import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Brain,
  Clock,
  MapPin,
  RefreshCw,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeading } from "@/components/layout/page-heading";
import { OfflineSampleNotice } from "@/components/ui/offline-sample-notice";
import { Panel } from "@/components/ui/panel";
import { StatCard } from "@/components/ui/stat-card";
import { ConfidenceChip, ScoreChip } from "@/components/ui/score-chip";
import { SeverityBadge } from "@/components/badges";
import { accuracyData, latestPredictions, riskData } from "@/mocks/predictions";

const modelInfo: [string, string][] = [
  ["Algorithm", "Gradient Boosting"],
  ["Training Data", "1.8M Transactions"],
  ["Features", "47"],
  ["Validation Accuracy", "92%"],
  ["Last Trained", "10 Sep 2026"],
  ["Prediction Horizon", "24 Hours"],
];

export default function PredictionsPage() {
  return (
    <div className="space-y-6">
      <PageHeading
        title="Predictive Analytics"
        description="AI-driven risk predictions for proactive cybercrime intervention"
      >
        <span>Last Updated: 15 Sep 2026, 11:24 AM</span>
        <button
          type="button"
          className="flex size-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground"
        >
          <RefreshCw className="size-4" />
        </button>
      </PageHeading>

      <OfflineSampleNotice />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={BarChart3}
          tone="blue"
          value="92"
          label="Predictions Today"
          note="Across 14 districts"
        />
        <StatCard
          icon={AlertTriangle}
          tone="red"
          value="24"
          label="High Risk"
          note="Require attention"
        />
        <StatCard
          icon={MapPin}
          tone="orange"
          value="37"
          label="Risk Locations"
          note="Predicted locations"
        />
        <StatCard
          icon={Activity}
          tone="green"
          value="92%"
          label="Model Accuracy"
          note="Current validation score"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel
          icon={BarChart3}
          title="Risk Prediction Distribution"
          actions={
            <select className="rounded-md border border-border bg-card px-2 py-1 text-xs">
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
            </select>
          }
        >
          <div className="h-72 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="high" name="High Risk" fill="#dc4545" />
                <Bar dataKey="medium" name="Medium Risk" fill="#f39a18" />
                <Bar dataKey="low" name="Low Risk" fill="#21965f" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          icon={TrendingUp}
          title="Model Performance"
          actions={
            <span className="rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-700">
              Active
            </span>
          }
        >
          <div className="h-72 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={accuracyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis domain={[70, 100]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  name="Accuracy %"
                  stroke="#1558a6"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel
        icon={Brain}
        title="Prediction Model Information"
        subtitle="Production Model v2.4"
        actions={
          <span className="rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-700">
            Active
          </span>
        }
      >
        <div className="grid gap-x-6 gap-y-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
          {modelInfo.map(([label, value]) => (
            <div key={label}>
              <span className="block text-xs text-muted-foreground">
                {label}
              </span>
              <strong className="mt-1 block text-sm text-foreground">
                {value}
              </strong>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        icon={MapPin}
        title="Latest Location Predictions"
        actions={
          <Link
            href="/gis"
            className="flex items-center gap-1 text-xs font-medium text-primary"
          >
            View GIS Map <ArrowRight className="size-3.5" />
          </Link>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="px-5 py-3">Prediction ID</th>
                <th className="px-5 py-3">Location</th>
                <th className="px-5 py-3">District</th>
                <th className="px-5 py-3">Risk Score</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Prediction Window</th>
                <th className="px-5 py-3">Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {latestPredictions.map((prediction) => (
                <tr
                  key={prediction.id}
                  className="border-b border-border last:border-0 hover:bg-muted/50"
                >
                  <td className="px-5 py-3 font-semibold text-primary">
                    {prediction.id}
                  </td>
                  <td className="px-5 py-3 font-medium">
                    {prediction.location}
                  </td>
                  <td className="px-5 py-3">{prediction.district}</td>
                  <td className="px-5 py-3">
                    <ScoreChip score={prediction.score} level={prediction.risk} />
                  </td>
                  <td className="px-5 py-3">
                    <ConfidenceChip level={prediction.confidence} />
                  </td>
                  <td className="px-5 py-3">
                    <span className="flex items-center gap-1.5">
                      <Clock className="size-3.5 text-muted-foreground" />
                      {prediction.window}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <SeverityBadge level={prediction.risk} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/40 p-4 text-muted-foreground">
        <Brain className="mt-0.5 size-5 shrink-0 text-primary" />
        <p className="text-sm leading-relaxed">
          Predictions are generated using historical cybercrime patterns,
          transaction behaviour, location signals and other available features.
          They are intended to support investigation and proactive intervention
          and should not be treated as proof of criminal activity.
        </p>
      </div>
    </div>
  );
}