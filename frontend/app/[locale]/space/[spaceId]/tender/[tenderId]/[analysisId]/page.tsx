"use client"

import { useEffect, useState, use } from "react"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Loader2, AlertCircle } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useTranslations } from "next-intl"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const BACKEND_URL = "/api/backend"; 

const formatKey = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// A new component to render Key-Value pairs in an expandable table
const KeyValueExpandableTable = ({ data }: { data: object }) => {
  return (
    <Table className="my-1 border bg-muted/20">
      <TableBody>
        {Object.entries(data).map(([key, value]) => {
          return (
            <TableRow key={key}>
              <TableCell className="font-semibold w-1/3 p-2 align-top border-r border-dashed border-muted/50">{formatKey(key)}</TableCell>
              <TableCell className="p-2">
                <div className={'whitespace-normal'}>
                  <DataRenderer data={value} />
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

// Recursive component to render complex data within cells
const DataRenderer = ({ data }: { data: any }) => {
  if (data === null || data === undefined) {
    return <span className="text-muted-foreground">N/A</span>;
  }

  // Handle arrays
  if (Array.isArray(data)) {
    // If it's a simple array of primitives, join them
    if (data.length > 0 && typeof data[0] !== 'object') {
        return `[${data.join(', ')}]`;
    }
    // If it's an array of objects, render each object recursively
    return (
      <div className="space-y-2">
        {data.map((item, index) => (
          <div key={index} className="p-2 border rounded-md bg-muted/20">
            <DataRenderer data={item} />
          </div>
        ))}
      </div>
    );
  }

  // Handle objects
  if (typeof data === 'object') {
     return <KeyValueExpandableTable data={data} />;
  }

  // Handle primitive values
  return String(data);
};


const ExpandableTable = ({ value }: { value: any[] }) => {
  if (!value || value.length === 0) return null;
  const headers = Object.keys(value[0]);

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            {headers.map((header, index) => (
              <TableHead 
                key={header} 
                className={`whitespace-nowrap font-bold text-center ${index < headers.length - 1 ? 'border-r border-dashed border-muted/50' : ''}`}
              >
                {formatKey(header)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {value.map((row: any, rowIndex: number) => {
            return (
              <TableRow key={rowIndex}>
                {headers.map((cellKey, index) => (
                  <TableCell 
                    key={cellKey}
                    className={index < headers.length - 1 ? 'border-r border-dashed border-muted/50' : ''}
                  >
                    <div className={'whitespace-normal'}>
                      <DataRenderer data={row[cellKey]} />
                    </div>
                  </TableCell>
                ))}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

const AnalysisDataRenderer = ({ data }: { data: any }) => {
  const ignoredKeys = ['_id', 'tender_id', 'created_at', 'id'];
  const topLevelKeys = Object.keys(data).filter(key => !ignoredKeys.includes(key));
  const defaultTab = topLevelKeys[0] || '';

  return (
    <Tabs defaultValue={defaultTab} className="w-full">
      <div className="overflow-x-auto pb-1">
        <TabsList className="inline-flex h-auto items-center justify-start space-x-2 bg-transparent p-1">
          {topLevelKeys.map(key => (
            <TabsTrigger 
              key={key} 
              value={key}
              className="flex-shrink-0 rounded-md px-4 py-2 text-sm font-medium text-muted-foreground ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
            >
              {formatKey(key)}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>

      {topLevelKeys.map(key => {
        const value = data[key];
        const isArrayOfObjects = Array.isArray(value) && value.length > 0 && typeof value[0] === 'object';

        return (
          <TabsContent key={key} value={key} className="mt-4">
            <Card className="border-border rounded-xl bg-card">
              <CardHeader>
                <CardTitle>{formatKey(key)}</CardTitle>
              </CardHeader>
              <CardContent>
                {isArrayOfObjects ? (
                  <ExpandableTable value={value} />
                ) : (
                  typeof value === 'object' && value !== null ? (
                    <Table className="my-2 border">
                      <TableBody>
                        {Object.entries(value).map(([objKey, objValue]) => (
                          <TableRow key={objKey}>
                            <TableCell className="font-semibold w-1/3">{formatKey(objKey)}</TableCell>
                            <TableCell><DataRenderer data={objValue} /></TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                     <p className="text-sm">{String(value)}</p>
                  )
                )}
              </CardContent>
            </Card>
          </TabsContent>
        );
      })}
    </Tabs>
  );
};


export default function AnalysisResultPage({ params: paramsPromise }: { params: Promise<{ spaceId: string, tenderId: string, analysisId: string }> }) {
  const t = useTranslations("AnalysisResultPage");
  const { accessToken } = useAuth();
  const { spaceId, tenderId, analysisId } = use(paramsPromise);

  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [tenderName, setTenderName] = useState<string>('');
  const [analysisName, setAnalysisName] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken || !analysisId) return;

    const fetchAllData = async () => {
      setLoading(true);
      setError(null);
      try {
        // 1. Fetch Analysis Result
        const analysisResponse = await fetch(`${BACKEND_URL}/analysis-results/${analysisId}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });

        if (!analysisResponse.ok) {
          const errorData = await analysisResponse.json();
          throw new Error(errorData.detail || t('errors.fetchResult'));
        }
        const analysisData = await analysisResponse.json();
        setAnalysisResult(analysisData); // This is the data for the renderer

        // 2. Fetch Tender data to get names
        if (analysisData.tender_id) {
          const tenderResponse = await fetch(`${BACKEND_URL}/tenders/${analysisData.tender_id}`, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });
          if (tenderResponse.ok) {
            const tenderData = await tenderResponse.json();
            setTenderName(tenderData.name);

            // 3. Determine the correct name for the title
            const placeholder = tenderData.analysis_results.find((r: any) => r.id === analysisId);
            const finalName = analysisData.name || placeholder?.name;
            setAnalysisName(finalName);
          }
        } else {
            setAnalysisName(analysisData.name || t('title'));
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, [accessToken, analysisId, t]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background p-6">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center bg-background p-6">
        <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
        <Link href={`/space/${spaceId}/tender/${tenderId}`}>
          <Button variant="default" className="mt-4">
            {t('errors.goBack')}
          </Button>
        </Link>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-6 py-10 flex-1 w-full">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            {analysisName || t('title')}
          </h1>
          {analysisResult && (
            <>
              {tenderName && (
                <p className="text-sm text-muted-foreground mt-2">
                  {t('tenderLabel', { name: tenderName })}
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                {t('createdLabel', { date: new Date(analysisResult.created_at).toLocaleString() })}
              </p>
            </>
          )}
        </div>
        <Link href={`/space/${spaceId}/tender/${tenderId}`}>
            <Button variant="default">
                {t('backButton')}
            </Button>
        </Link>
      </div>
      <div>
        {analysisResult ? (
          <AnalysisDataRenderer data={analysisResult} />
        ) : (
          <p>{t('noData')}</p>
        )}
      </div>
    </main>
  );
}
