import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Lightbulb, 
  AlertTriangle, 
  BookOpen, 
  HelpCircle, 
  Copy, 
  Loader2,
  CheckCircle2,
  XCircle
} from 'lucide-react'
import api from '@/services/api'

interface Claim {
  text: string
  type: string
  confidence: number
  entities: string[]
  metrics: { value: string; unit: string }[]
  verifiable: boolean
  evidence_needed: string[]
}

interface Contradiction {
  claim1: string
  claim2: string
  source1: string
  source2: string
  type: string
  severity: string
  confidence: number
  explanation: string
  resolution_suggestions: string[]
}

interface ResearchQuestion {
  question: string
  type: string
  relevance_score: number
  source_concepts: string[]
  rationale: string
  suggested_methods: string[]
}

interface Recommendation {
  document_id: string
  title: string
  score: number
  type: string
  reasons: string[]
  explanation: string
}

export default function Analysis() {
  const [activeTab, setActiveTab] = useState('claims')
  const [isLoading, setIsLoading] = useState(false)
  
  // Claims state
  const [claimText, setClaimText] = useState('')
  const [claims, setClaims] = useState<Claim[]>([])
  
  // Research questions state
  const [concepts, setConcepts] = useState('')
  const [questions, setQuestions] = useState<ResearchQuestion[]>([])
  
  // Contradiction state
  const [docId1, setDocId1] = useState('')
  const [docId2, setDocId2] = useState('')
  const [contradictions, setContradictions] = useState<Contradiction[]>([])
  
  // Recommendations state
  const [recDocId, setRecDocId] = useState('')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])

  // Extract claims
  const handleExtractClaims = async () => {
    if (!claimText.trim()) return
    setIsLoading(true)
    try {
      const response = await api.post('/api/advanced/claims/extract', {
        text: claimText,
        top_k: 10
      })
      setClaims(response.data)
    } catch (error) {
      console.error('Failed to extract claims:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Generate research questions
  const handleGenerateQuestions = async () => {
    if (!concepts.trim()) return
    setIsLoading(true)
    try {
      const conceptList = concepts.split(',').map(c => c.trim()).filter(c => c)
      const response = await api.post('/api/advanced/questions/generate', {
        concepts: conceptList,
        num_questions: 10
      })
      setQuestions(response.data)
    } catch (error) {
      console.error('Failed to generate questions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Detect contradictions
  const handleDetectContradictions = async () => {
    if (!docId1.trim() || !docId2.trim()) return
    setIsLoading(true)
    try {
      const response = await api.post('/api/advanced/contradictions/detect', {
        document_id_1: docId1,
        document_id_2: docId2
      })
      setContradictions(response.data)
    } catch (error) {
      console.error('Failed to detect contradictions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Get recommendations
  const handleGetRecommendations = async () => {
    if (!recDocId.trim()) return
    setIsLoading(true)
    try {
      const response = await api.get(`/api/advanced/recommendations/${recDocId}`)
      setRecommendations(response.data)
    } catch (error) {
      console.error('Failed to get recommendations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getClaimTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      performance: 'bg-green-500',
      comparison: 'bg-blue-500',
      contribution: 'bg-purple-500',
      finding: 'bg-yellow-500',
      limitation: 'bg-red-500',
      hypothesis: 'bg-orange-500',
    }
    return colors[type] || 'bg-gray-500'
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'text-red-600 bg-red-100',
      high: 'text-orange-600 bg-orange-100',
      medium: 'text-yellow-600 bg-yellow-100',
      low: 'text-green-600 bg-green-100',
    }
    return colors[severity] || 'text-gray-600 bg-gray-100'
  }

  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Advanced Analysis</h1>
        <p className="text-muted-foreground">
          Extract claims, detect contradictions, generate questions, and get recommendations
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="h-[calc(100%-5rem)]">
        <TabsList className="mb-4">
          <TabsTrigger value="claims" className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Claim Extraction
          </TabsTrigger>
          <TabsTrigger value="contradictions" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Contradictions
          </TabsTrigger>
          <TabsTrigger value="questions" className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4" />
            Research Questions
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Recommendations
          </TabsTrigger>
        </TabsList>

        {/* Claim Extraction Tab */}
        <TabsContent value="claims" className="h-full">
          <div className="grid grid-cols-2 gap-6 h-full">
            <Card>
              <CardHeader>
                <CardTitle>Extract Claims</CardTitle>
                <CardDescription>
                  Paste text to extract verifiable claims like performance metrics, comparisons, and findings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Paste academic text here to extract claims..."
                  className="min-h-[300px] mb-4"
                  value={claimText}
                  onChange={(e) => setClaimText(e.target.value)}
                />
                <Button onClick={handleExtractClaims} disabled={isLoading || !claimText.trim()}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Lightbulb className="h-4 w-4 mr-2" />}
                  Extract Claims
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Extracted Claims ({claims.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {claims.map((claim, i) => (
                      <Card key={i} className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <Badge className={getClaimTypeBadge(claim.type)}>{claim.type}</Badge>
                          <div className="flex items-center gap-2">
                            {claim.verifiable ? (
                              <Badge variant="outline" className="text-green-600">
                                <CheckCircle2 className="h-3 w-3 mr-1" /> Verifiable
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-gray-500">
                                <XCircle className="h-3 w-3 mr-1" /> Unverifiable
                              </Badge>
                            )}
                            <span className="text-sm text-muted-foreground">
                              {(claim.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <p className="text-sm mb-2">{claim.text}</p>
                        {claim.metrics.length > 0 && (
                          <div className="flex gap-2 mb-2">
                            {claim.metrics.map((m, j) => (
                              <Badge key={j} variant="secondary">
                                {m.value}{m.unit}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {claim.entities.length > 0 && (
                          <p className="text-xs text-muted-foreground">
                            Entities: {claim.entities.join(', ')}
                          </p>
                        )}
                      </Card>
                    ))}
                    {claims.length === 0 && (
                      <p className="text-muted-foreground text-center py-8">
                        No claims extracted yet. Paste text and click "Extract Claims"
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Contradictions Tab */}
        <TabsContent value="contradictions" className="h-full">
          <div className="grid grid-cols-2 gap-6 h-full">
            <Card>
              <CardHeader>
                <CardTitle>Detect Contradictions</CardTitle>
                <CardDescription>
                  Compare two documents to find conflicting claims
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Document 1 ID</Label>
                    <Input 
                      placeholder="Enter first document ID"
                      value={docId1}
                      onChange={(e) => setDocId1(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Document 2 ID</Label>
                    <Input 
                      placeholder="Enter second document ID"
                      value={docId2}
                      onChange={(e) => setDocId2(e.target.value)}
                    />
                  </div>
                  <Button onClick={handleDetectContradictions} disabled={isLoading || !docId1 || !docId2}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <AlertTriangle className="h-4 w-4 mr-2" />}
                    Detect Contradictions
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Found Contradictions ({contradictions.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {contradictions.map((c, i) => (
                      <Card key={i} className="p-4 border-l-4 border-l-red-500">
                        <div className="flex items-center justify-between mb-2">
                          <Badge className={getSeverityColor(c.severity)}>
                            {c.severity.toUpperCase()}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {(c.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <div className="space-y-2 mb-3">
                          <div className="bg-muted p-2 rounded text-sm">
                            <p className="font-medium text-xs text-muted-foreground mb-1">{c.source1}:</p>
                            {c.claim1}
                          </div>
                          <div className="flex justify-center">
                            <AlertTriangle className="h-4 w-4 text-red-500" />
                          </div>
                          <div className="bg-muted p-2 rounded text-sm">
                            <p className="font-medium text-xs text-muted-foreground mb-1">{c.source2}:</p>
                            {c.claim2}
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{c.explanation}</p>
                        <details className="text-xs">
                          <summary className="cursor-pointer text-muted-foreground">Resolution suggestions</summary>
                          <ul className="mt-2 space-y-1 pl-4">
                            {c.resolution_suggestions.map((s, j) => (
                              <li key={j}>• {s}</li>
                            ))}
                          </ul>
                        </details>
                      </Card>
                    ))}
                    {contradictions.length === 0 && (
                      <p className="text-muted-foreground text-center py-8">
                        No contradictions found yet. Enter document IDs to compare.
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Research Questions Tab */}
        <TabsContent value="questions" className="h-full">
          <div className="grid grid-cols-2 gap-6 h-full">
            <Card>
              <CardHeader>
                <CardTitle>Generate Research Questions</CardTitle>
                <CardDescription>
                  Enter concepts to generate relevant research questions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Concepts (comma-separated)</Label>
                    <Textarea
                      placeholder="e.g., transformers, attention mechanism, BERT, language models"
                      className="min-h-[150px]"
                      value={concepts}
                      onChange={(e) => setConcepts(e.target.value)}
                    />
                  </div>
                  <Button onClick={handleGenerateQuestions} disabled={isLoading || !concepts.trim()}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <HelpCircle className="h-4 w-4 mr-2" />}
                    Generate Questions
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Generated Questions ({questions.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {questions.map((q, i) => (
                      <Card key={i} className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <Badge variant="outline">{q.type}</Badge>
                          <Button variant="ghost" size="sm" onClick={() => navigator.clipboard.writeText(q.question)}>
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                        <p className="font-medium mb-2">{q.question}</p>
                        <p className="text-sm text-muted-foreground mb-2">{q.rationale}</p>
                        <div className="flex flex-wrap gap-1 mb-2">
                          {q.source_concepts.map((c, j) => (
                            <Badge key={j} variant="secondary" className="text-xs">{c}</Badge>
                          ))}
                        </div>
                        <details className="text-xs">
                          <summary className="cursor-pointer text-muted-foreground">Suggested methods</summary>
                          <ul className="mt-2 space-y-1 pl-4">
                            {q.suggested_methods.map((m, j) => (
                              <li key={j}>• {m}</li>
                            ))}
                          </ul>
                        </details>
                      </Card>
                    ))}
                    {questions.length === 0 && (
                      <p className="text-muted-foreground text-center py-8">
                        No questions generated yet. Enter concepts to generate.
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="h-full">
          <div className="grid grid-cols-2 gap-6 h-full">
            <Card>
              <CardHeader>
                <CardTitle>Get Recommendations</CardTitle>
                <CardDescription>
                  Enter a document ID to get related paper recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Document ID</Label>
                    <Input 
                      placeholder="Enter document ID"
                      value={recDocId}
                      onChange={(e) => setRecDocId(e.target.value)}
                    />
                  </div>
                  <Button onClick={handleGetRecommendations} disabled={isLoading || !recDocId.trim()}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <BookOpen className="h-4 w-4 mr-2" />}
                    Get Recommendations
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recommendations ({recommendations.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {recommendations.map((rec, i) => (
                      <Card key={i} className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-medium">{rec.title || rec.document_id}</p>
                            <p className="text-xs text-muted-foreground">{rec.document_id}</p>
                          </div>
                          <Badge variant="outline">
                            {(rec.score * 100).toFixed(0)}% match
                          </Badge>
                        </div>
                        <Badge className="mb-2">{rec.type}</Badge>
                        <p className="text-sm text-muted-foreground mb-2">{rec.explanation}</p>
                        <div className="text-xs text-muted-foreground">
                          {rec.reasons.slice(0, 2).map((r, j) => (
                            <p key={j}>• {r}</p>
                          ))}
                        </div>
                      </Card>
                    ))}
                    {recommendations.length === 0 && (
                      <p className="text-muted-foreground text-center py-8">
                        No recommendations yet. Enter a document ID.
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
