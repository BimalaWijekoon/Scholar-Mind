import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useThemeStore } from '@/store/themeStore'
import { Moon, Sun, Save, Loader2 } from 'lucide-react'

export default function Settings() {
  const { theme, toggleTheme } = useThemeStore()
  const [isSaving, setIsSaving] = useState(false)
  
  const [settings, setSettings] = useState({
    apiKey: '',
    neo4jUri: '',
    neo4jUser: '',
    neo4jPassword: '',
    embeddingModel: 'all-MiniLM-L6-v2',
    chunkSize: 512,
    chunkOverlap: 50,
  })

  const handleSave = async () => {
    setIsSaving(true)
    
    // Simulate saving
    await new Promise((resolve) => setTimeout(resolve, 1000))
    
    setIsSaving(false)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure your ScholarMind instance
        </p>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>
            Customize the look and feel
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Theme</p>
              <p className="text-sm text-muted-foreground">
                Switch between light and dark mode
              </p>
            </div>
            <Button variant="outline" onClick={toggleTheme}>
              {theme === 'dark' ? (
                <>
                  <Sun className="h-4 w-4 mr-2" />
                  Light
                </>
              ) : (
                <>
                  <Moon className="h-4 w-4 mr-2" />
                  Dark
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>
            Configure external API connections
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Google API Key</label>
            <Input
              type="password"
              placeholder="Enter your API key"
              value={settings.apiKey}
              onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
              className="mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Required for Gemini 2.0 Flash
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Database Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Database Configuration</CardTitle>
          <CardDescription>
            Configure Neo4j connection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Neo4j URI</label>
            <Input
              placeholder="bolt://localhost:7687"
              value={settings.neo4jUri}
              onChange={(e) => setSettings({ ...settings, neo4jUri: e.target.value })}
              className="mt-1"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Username</label>
              <Input
                placeholder="neo4j"
                value={settings.neo4jUser}
                onChange={(e) => setSettings({ ...settings, neo4jUser: e.target.value })}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                placeholder="Password"
                value={settings.neo4jPassword}
                onChange={(e) => setSettings({ ...settings, neo4jPassword: e.target.value })}
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Processing Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Settings</CardTitle>
          <CardDescription>
            Configure document processing
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Embedding Model</label>
            <Input
              placeholder="all-MiniLM-L6-v2"
              value={settings.embeddingModel}
              onChange={(e) => setSettings({ ...settings, embeddingModel: e.target.value })}
              className="mt-1"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Chunk Size</label>
              <Input
                type="number"
                value={settings.chunkSize}
                onChange={(e) => setSettings({ ...settings, chunkSize: parseInt(e.target.value) })}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Chunk Overlap</label>
              <Input
                type="number"
                value={settings.chunkOverlap}
                onChange={(e) => setSettings({ ...settings, chunkOverlap: parseInt(e.target.value) })}
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
