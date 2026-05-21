import { useState } from 'react'
import { FileText, Trash, RefreshCw, Eye, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import FileUpload from '@/components/FileUpload'
import { useDocumentStore } from '@/store/documentStore'
import { cn } from '@/utils/cn'

export default function Documents() {
  const { documents, removeDocument } = useDocumentStore()
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())

  const handleReprocess = async (docId: string) => {
    setProcessingIds((prev) => new Set(prev).add(docId))
    
    // Simulate reprocessing
    await new Promise((resolve) => setTimeout(resolve, 2000))
    
    setProcessingIds((prev) => {
      const next = new Set(prev)
      next.delete(docId)
      return next
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-500 bg-green-500/10'
      case 'processing':
        return 'text-blue-500 bg-blue-500/10'
      case 'pending':
        return 'text-yellow-500 bg-yellow-500/10'
      case 'failed':
        return 'text-red-500 bg-red-500/10'
      default:
        return 'text-muted-foreground bg-muted'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="text-muted-foreground mt-1">
          Upload and manage your research documents
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Upload PDFs, text files, or Markdown documents to analyze
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FileUpload />
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle>Document Library</CardTitle>
          <CardDescription>
            {documents.length} documents in your library
          </CardDescription>
        </CardHeader>
        <CardContent>
          {documents.length > 0 ? (
            <div className="divide-y">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
                >
                  <FileText className="h-10 w-10 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{doc.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={cn(
                          'text-xs px-2 py-0.5 rounded-full',
                          getStatusColor(doc.status)
                        )}
                      >
                        {doc.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {doc.fileType}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleReprocess(doc.id)}
                      disabled={processingIds.has(doc.id)}
                    >
                      {processingIds.has(doc.id) ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeDocument(doc.id)}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No documents yet</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Upload your first document to get started
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
