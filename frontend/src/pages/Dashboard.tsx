import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, MessageSquare, Network, Search, TrendingUp, Clock } from 'lucide-react'
import { useDocumentStore } from '@/store/documentStore'
import { useGraphStore } from '@/store/graphStore'

export default function Dashboard() {
  const { documents } = useDocumentStore()
  const { nodes, edges } = useGraphStore()

  const stats = [
    {
      title: 'Total Documents',
      value: documents.length,
      description: 'Uploaded to the system',
      icon: FileText,
      color: 'text-blue-500',
    },
    {
      title: 'Knowledge Entities',
      value: nodes.length,
      description: 'Extracted from documents',
      icon: Network,
      color: 'text-green-500',
    },
    {
      title: 'Relationships',
      value: edges.length,
      description: 'Connections discovered',
      icon: TrendingUp,
      color: 'text-purple-500',
    },
    {
      title: 'Queries Today',
      value: 0,
      description: 'Questions answered',
      icon: MessageSquare,
      color: 'text-orange-500',
    },
  ]

  const recentDocuments = documents.slice(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your research assistant
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Documents */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
            <CardDescription>
              Latest documents added to your library
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentDocuments.length > 0 ? (
              <div className="space-y-4">
                {recentDocuments.map((doc) => (
                  <div key={doc.id} className="flex items-center gap-4">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {doc.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {doc.status}
                      </p>
                    </div>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-sm text-muted-foreground">
                  No documents yet. Upload your first document to get started.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks to help you get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <a
                href="/documents"
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors"
              >
                <FileText className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="text-sm font-medium">Upload Documents</p>
                  <p className="text-xs text-muted-foreground">
                    Add PDFs, papers, or articles
                  </p>
                </div>
              </a>
              <a
                href="/chat"
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors"
              >
                <MessageSquare className="h-8 w-8 text-green-500" />
                <div>
                  <p className="text-sm font-medium">Ask Questions</p>
                  <p className="text-xs text-muted-foreground">
                    Chat with your documents
                  </p>
                </div>
              </a>
              <a
                href="/graph"
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors"
              >
                <Network className="h-8 w-8 text-purple-500" />
                <div>
                  <p className="text-sm font-medium">Explore Knowledge Graph</p>
                  <p className="text-xs text-muted-foreground">
                    Visualize connections
                  </p>
                </div>
              </a>
              <a
                href="/search"
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors"
              >
                <Search className="h-8 w-8 text-orange-500" />
                <div>
                  <p className="text-sm font-medium">Search</p>
                  <p className="text-xs text-muted-foreground">
                    Find specific information
                  </p>
                </div>
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
