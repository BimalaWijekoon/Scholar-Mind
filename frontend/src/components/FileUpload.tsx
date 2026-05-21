import { useState, useRef } from 'react'
import { Upload, File, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/utils/cn'
import { useDocumentStore } from '@/store/documentStore'
import { documentService } from '@/services/api'

interface UploadedFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
}

export default function FileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { addDocument } = useDocumentStore()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      addFiles(selectedFiles)
    }
  }

  const addFiles = (newFiles: File[]) => {
    const uploadedFiles: UploadedFile[] = newFiles.map((file) => ({
      file,
      progress: 0,
      status: 'pending',
    }))
    
    setFiles((prev) => [...prev, ...uploadedFiles])
    
    // Start uploading
    uploadedFiles.forEach((uploadedFile, index) => {
      uploadFile(uploadedFile, files.length + index)
    })
  }

  const uploadFile = async (uploadedFile: UploadedFile, index: number) => {
    try {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: 'uploading' } : f
        )
      )

      const result = await documentService.upload(uploadedFile.file, (progress) => {
        setFiles((prev) =>
          prev.map((f, i) =>
            i === index ? { ...f, progress } : f
          )
        )
      })

      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: 'completed', progress: 100 } : f
        )
      )

      addDocument(result)
    } catch (error) {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index
            ? { ...f, status: 'error', error: 'Upload failed' }
            : f
        )
      )
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer',
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        )}
      >
        <Upload className="h-10 w-10 text-muted-foreground mb-4" />
        <p className="text-sm text-muted-foreground text-center">
          <span className="font-medium text-foreground">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          PDF, TXT, MD, HTML (max 50MB)
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.md,.html"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, index) => (
            <Card key={index}>
              <CardContent className="flex items-center gap-4 p-4">
                <File className="h-8 w-8 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{file.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {file.status === 'uploading' && (
                    <Progress value={file.progress} className="mt-2 h-1" />
                  )}
                  {file.status === 'error' && (
                    <p className="text-xs text-destructive mt-1">{file.error}</p>
                  )}
                </div>
                {file.status === 'uploading' ? (
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                ) : (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile(index)
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
