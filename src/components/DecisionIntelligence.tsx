import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";

interface DecisionCard {
    id: string;
    title: string;
    why: string;
    riskReduced: string;
    riskLevel: "Low" | "Medium" | "High";
    tradeoff: string;
    costImpact: string;
    confidence: string;
}

interface DecisionIntelligenceData {
    error?: boolean;
    message?: string;
    decisions: DecisionCard[];
    totalMonthlyCostEstimate: string;
    architectureComplexity: string;
    costBreakdown: string[];
}

interface DecisionIntelligenceProps {
    data: DecisionIntelligenceData;
}

const RiskBadge = ({ level }: { level: string }) => {
    const colors = {
        High: "bg-green-100 text-green-800 border-green-300",
        Medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
        Low: "bg-blue-100 text-blue-800 border-blue-300",
    };

    return (
        <Badge variant="outline" className={colors[level as keyof typeof colors] || colors.Low}>
            Risk Reduced: {level}
        </Badge>
    );
};

const DecisionCardComponent = ({ decision }: { decision: DecisionCard }) => {
    return (
        <Card className="mb-4 hover:shadow-lg transition-shadow">
            <CardHeader>
                <div className="flex items-start justify-between">
                    <CardTitle className="text-lg font-semibold">{decision.title}</CardTitle>
                    <RiskBadge level={decision.riskLevel} />
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-2xl">💡</span>
                        <h4 className="font-semibold text-sm text-gray-700">Why This Decision</h4>
                    </div>
                    <p className="text-sm text-gray-600 pl-8">{decision.why}</p>
                </div>

                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-2xl">🛡️</span>
                        <h4 className="font-semibold text-sm text-gray-700">Risk Reduced</h4>
                    </div>
                    <p className="text-sm text-gray-600 pl-8">{decision.riskReduced}</p>
                </div>

                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-2xl">⚖️</span>
                        <h4 className="font-semibold text-sm text-gray-700">Tradeoff</h4>
                    </div>
                    <p className="text-sm text-gray-600 pl-8">{decision.tradeoff}</p>
                </div>

                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-2xl">💰</span>
                        <h4 className="font-semibold text-sm text-gray-700">Cost Impact</h4>
                    </div>
                    <p className="text-sm font-medium text-gray-800 pl-8">{decision.costImpact}</p>
                </div>

                <div className="pt-2 border-t">
                    <p className="text-xs text-gray-500">
                        Confidence: <span className="font-semibold">{decision.confidence}</span>
                    </p>
                </div>
            </CardContent>
        </Card>
    );
};

export function DecisionIntelligence({ data }: DecisionIntelligenceProps) {
    // Handle error state
    if (data?.error) {
        return (
            <div className="p-6">
                <Alert variant="destructive">
                    <AlertDescription>
                        {data.message || "Decision insights temporarily unavailable"}
                    </AlertDescription>
                </Alert>
            </div>
        );
    }

    // Handle no decisions
    if (!data?.decisions || data.decisions.length === 0) {
        return (
            <div className="p-6">
                <Alert>
                    <AlertDescription>
                        No architectural decisions detected. Try generating a more complex infrastructure.
                    </AlertDescription>
                </Alert>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6 bg-gray-50">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">
                        🎯 Architecture Decisions
                    </h2>
                    <p className="text-gray-600">
                        Understanding the <span className="font-semibold">WHY</span> behind your infrastructure
                    </p>
                </div>

                {/* Decision Cards */}
                <div className="space-y-4 mb-8">
                    {data.decisions.map((decision) => (
                        <DecisionCardComponent key={decision.id} decision={decision} />
                    ))}
                </div>

                <Separator className="my-8" />

                {/* Cost Summary */}
                <Card className="bg-white">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <span className="text-2xl">💰</span>
                            Cost Summary
                        </CardTitle>
                        <CardDescription>
                            Estimated monthly infrastructure costs
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                            <span className="font-semibold text-gray-700">Total Estimated Cost</span>
                            <span className="text-2xl font-bold text-blue-600">
                                {data.totalMonthlyCostEstimate}
                            </span>
                        </div>

                        {data.costBreakdown && data.costBreakdown.length > 0 && (
                            <div className="space-y-2">
                                <h4 className="font-semibold text-sm text-gray-700">Breakdown</h4>
                                <ul className="space-y-1">
                                    {data.costBreakdown.map((item, index) => (
                                        <li key={index} className="text-sm text-gray-600 flex items-center gap-2">
                                            <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <div className="pt-4 border-t">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-600">Architecture Complexity</span>
                                <Badge variant="outline" className="font-semibold">
                                    {data.architectureComplexity}
                                </Badge>
                            </div>
                        </div>

                        <Alert className="bg-yellow-50 border-yellow-200">
                            <AlertDescription className="text-xs text-yellow-800">
                                💡 Cost estimates are approximate and based on US East (N. Virginia) region pricing.
                                Actual costs may vary based on usage, data transfer, and region.
                            </AlertDescription>
                        </Alert>
                    </CardContent>
                </Card>

                {/* Footer Note */}
                <div className="mt-8 p-4 bg-white rounded-lg border border-gray-200">
                    <p className="text-xs text-gray-500 text-center">
                        <span className="font-semibold">Infrastructure Decision Intelligence</span> helps you understand
                        the rationale behind architectural choices, enabling better communication with stakeholders
                        and informed decision-making.
                    </p>
                </div>
            </div>
        </div>
    );
}
