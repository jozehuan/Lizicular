"use client"

import { useEffect, useState, use, useRef } from "react"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, AlertCircle, Pencil, Download } from "lucide-react"
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFileExcel } from '@fortawesome/free-solid-svg-icons'
import Link from "next/link"
import * as XLSX from 'xlsx'

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useTranslations } from "next-intl"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardFooter } from "@/components/dashboard/footer"

const BACKEND_URL = "/api/backend"; 

const formatKey = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// A new component to render Key-Value pairs in an expandable table
const KeyValueExpandableTable = ({ data }: { data: object }) => {
  return (
    <div className="overflow-x-auto scrollbar-show border rounded-md">
      <Table className="my-1 bg-muted/20 min-w-full">
        <TableBody>
          {Object.entries(data)
            .filter(([_, value]) => value !== null)
            .map(([key, value]) => {
              return (
                <TableRow key={key}>
                  <TableCell className="font-semibold w-1/3 min-w-[150px] p-2 align-top border-r border-dashed border-muted/50">{formatKey(key)}</TableCell>
                  <TableCell className="p-2 min-w-[250px]">
                    <div className={'whitespace-normal'}>
                      <DataRenderer data={value} />
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
        </TableBody>
      </Table>
    </div>
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
    <div className="overflow-x-auto pb-4 scrollbar-show border rounded-xl">
      <Table className="min-w-full border-collapse">
        <TableHeader className="sticky top-0 bg-background z-10 shadow-sm">
          <TableRow>
            {headers.map((header, index) => (
              <TableHead 
                key={header} 
                className={`min-w-[200px] whitespace-nowrap font-bold text-center p-4 ${index < headers.length - 1 ? 'border-r border-dashed border-muted/50' : ''}`}
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
                    className={`min-w-[200px] p-4 align-top ${index < headers.length - 1 ? 'border-r border-dashed border-muted/50' : ''}`}
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
  const ignoredKeys = ['_id', 'tender_id', 'created_at', 'id', 'name'];
  const topLevelKeys = Object.keys(data).filter(key => 
    !ignoredKeys.includes(key) && data[key] !== null
  );
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
              <CardContent className="pt-6">
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

  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [isUpdatingName, setIsUpdatingName] = useState(false);

  const exportToExcel = () => {
    if (!analysisResult) return;

    const wb = XLSX.utils.book_new();
    const ignoredKeys = ['_id', 'tender_id', 'created_at', 'id', 'name', 'procedure_id', 'procedure_name', 'created_by', 'processing_time', 'status', 'error_message', 'data'];

    // 1. Helper to calculate vertical height (rows) needed for any node
    const getRowHeight = (data: any): number => {
      if (Array.isArray(data)) {
        return data.reduce((sum, item) => sum + getRowHeight(item), 0) || 1;
      }
      if (typeof data === 'object' && data !== null) {
        let maxHeight = 1;
        Object.values(data).forEach(val => {
          if (Array.isArray(val)) {
            maxHeight = Math.max(maxHeight, getRowHeight(val));
          }
        });
        return maxHeight;
      }
      return 1;
    };

    // 2. Helper to collect all unique headers in dot notation
    const collectHeaders = (data: any, prefix = '', headers = new Set<string>()) => {
      if (Array.isArray(data)) {
        data.forEach(item => collectHeaders(item, prefix, headers));
      } else if (typeof data === 'object' && data !== null) {
        Object.entries(data).forEach(([key, value]) => {
          const newPrefix = prefix ? `${prefix}.${key}` : key;
          if (Array.isArray(value)) {
            if (value.length === 0) headers.add(newPrefix);
            else collectHeaders(value, newPrefix, headers);
          } else if (typeof value === 'object' && value !== null) {
            collectHeaders(value, newPrefix, headers);
          } else {
            headers.add(newPrefix);
          }
        });
      }
      return headers;
    };

    // Process each main section of the analysis
    Object.entries(analysisResult).forEach(([key, value]) => {
      if (ignoredKeys.includes(key) || value === null) return;

      const sheetHeadersSet = collectHeaders(value);
      const headers = Array.from(sheetHeadersSet).sort();
      const headerMap: Record<string, number> = {};
      headers.forEach((h, i) => headerMap[h] = i);

      const rows: any[][] = [];
      const merges: XLSX.Range[] = [];

      // Add header row
      rows.push(headers.map(h => h.toUpperCase()));

      // 3. Main recursive function to fill rows and handle merges
      const fillData = (data: any, startRow: number, prefix = '') => {
        const height = getRowHeight(data);
        
        // Initialize rows if they don't exist
        for (let i = 0; i < height; i++) {
          if (!rows[startRow + i]) rows[startRow + i] = new Array(headers.length).fill(null);
        }

        if (Array.isArray(data)) {
          let currentR = startRow;
          data.forEach(item => {
            const itemHeight = getRowHeight(item);
            fillData(item, currentR, prefix);
            currentR += itemHeight;
          });
          return;
        }

        if (typeof data === 'object' && data !== null) {
          Object.entries(data).forEach(([k, v]) => {
            const newPrefix = prefix ? `${prefix}.${k}` : k;
            fillData(v, startRow, newPrefix);
          });
          return;
        }

        // Primitive value: place it and merge if height > 1
        const colIndex = headerMap[prefix];
        if (colIndex !== undefined) {
          rows[startRow][colIndex] = data;
          if (height > 1) {
            merges.push({
              s: { r: startRow, c: colIndex },
              e: { r: startRow + height - 1, c: colIndex }
            });
          }
        }
      };

      fillData(value, 1); // Start filling from row 1 (row 0 is header)

      if (rows.length > 1) {
        const ws = XLSX.utils.aoa_to_sheet(rows);
        ws['!merges'] = merges;
        
        // Basic column width adjustment
        const wscols = headers.map(() => ({ wch: 20 }));
        ws['!cols'] = wscols;

        XLSX.utils.book_append_sheet(wb, ws, formatKey(key).substring(0, 31));
      }
    });

    const fileName = `${analysisName || 'analysis'}_export.xlsx`.replace(/[\/\\?%*:|"<>]/g, '-');
    XLSX.writeFile(wb, fileName);
  };

  const handleUpdateName = async () => {
    if (!editedName.trim() || editedName === analysisName) {
      setIsEditingName(false);
      return;
    }

    setIsUpdatingName(true);
    try {
      const response = await fetch(`${BACKEND_URL}/analysis-results/${analysisId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ name: editedName.trim() }),
      });

      if (!response.ok) {
        throw new Error('Failed to update name');
      }

      setAnalysisName(editedName.trim());
      setIsEditingName(false);
    } catch (err) {
      console.error('Error updating name:', err);
      // Fallback: reset editedName to current name on failure
      setEditedName(analysisName);
    } finally {
      setIsUpdatingName(false);
    }
  };

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
            setEditedName(finalName);
          }
        } else {
            const finalName = analysisData.name || t('title');
            setAnalysisName(finalName);
            setEditedName(finalName);
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
    <div className="min-h-screen bg-background flex flex-col">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-10 flex-1 w-full">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div className="w-full sm:w-auto flex-1">
            {isEditingName ? (
              <div className="flex items-center gap-2 w-full">
                <Input
                  value={editedName}
                  onChange={(e) => setEditedName(e.target.value)}
                  onBlur={handleUpdateName}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleUpdateName();
                    if (e.key === 'Escape') {
                      setIsEditingName(false);
                      setEditedName(analysisName);
                    }
                  }}
                  className="text-xl sm:text-2xl font-semibold h-10 w-full max-w-[300px]"
                  autoFocus
                  disabled={isUpdatingName}
                  maxLength={50}
                />
                {isUpdatingName && <Loader2 className="h-5 w-5 animate-spin text-primary shrink-0" />}
              </div>
            ) : (
              <div className="flex items-center gap-2 group w-full">
                <h1 
                  className="text-xl sm:text-2xl font-semibold text-foreground cursor-pointer hover:text-primary transition-colors break-words"
                  onDoubleClick={() => setIsEditingName(true)}
                >
                  {analysisName || t('title')}
                </h1>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 shrink-0 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity"
                  onClick={() => setIsEditingName(true)}
                >
                  < Pencil className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            )}
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
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={exportToExcel}
                    disabled={!analysisResult}
                    className="flex items-center justify-center h-9 w-9 p-0 transition-all duration-200 disabled:opacity-30 cursor-pointer"
                  >
                    <FontAwesomeIcon 
                      icon={faFileExcel} 
                      className="text-green-600 hover:text-green-400 active:text-green-300 transition-colors"
                      style={{ width: '28px', height: '28px' }}
                    />
                    <span className="sr-only">Exportar a Excel</span>
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Exportar a Excel</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <Link href={`/space/${spaceId}/tender/${tenderId}`}>
              <Button variant="default">
                {t('backButton')}
              </Button>
            </Link>
          </div>
        </div>

        <div>
          {analysisResult ? (
            <AnalysisDataRenderer data={analysisResult} />
          ) : (
            <p>{t('noData')}</p>
          )}
        </div>
      </main>
      <DashboardFooter />
    </div>
  );
}
