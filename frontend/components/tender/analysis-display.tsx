"use client"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle, Clock, FileJson, Info } from "lucide-react"

// Interfaces based on backend/tenders/schemas.py
interface InformacionGeneral {
  requisito: string
  detalle: string
  referencia: string
}

interface Requisito {
  requisito: string
  detalle: string
  referencia: string
}

interface OtroRequisito {
  requisito: string
  detalle: string
  referencia: string
}

interface Subcriterio {
  nombre: string
  detalle: string
  puntuacion: number
  referencia: string
}

interface CriterioNoMatematico {
  nombre: string
  detalle: string
  puntuacion_total: number
  referencia: string
  subcriterios: Subcriterio[]
}

interface Variable {
  simbolo: string
  detalle: string
}

interface Formula {
  formula: string
  detalle_formula: string
  variables: Variable[]
}

interface CriterioMatematico {
  nombre: string
  detalle: string
  puntuacion: number
  referencia: string
  formula: Formula
}

interface AnalysisData {
  informacion_general: InformacionGeneral[]
  requisitos: Requisito[]
  otros_requisitos: OtroRequisito[]
  criterios_no_matematicos: CriterioNoMatematico[]
  criterios_matematicos: CriterioMatematico[]
}

interface AnalysisResult {
  id: string
  name: string
  procedure_name: string
  created_at: string
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
  data: AnalysisData
}

interface AnalysisDisplayProps {
  analysisResults: AnalysisResult[]
}

const getStatusIcon = (status: AnalysisResult["status"]) => {
  switch (status) {
    case "COMPLETED":
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case "PROCESSING":
      return <Clock className="h-5 w-5 text-blue-500" />
    case "FAILED":
      return <AlertCircle className="h-5 w-5 text-red-500" />
    default:
      return <Clock className="h-5 w-5 text-gray-500" />
  }
}

export function AnalysisDisplay({ analysisResults }: AnalysisDisplayProps) {
  if (!analysisResults || analysisResults.length === 0) {
    return (
      <Card className="text-center">
        <CardHeader>
          <FileJson className="mx-auto h-12 w-12 text-gray-400" />
        </CardHeader>
        <CardContent>
          <CardTitle>No Analysis Available</CardTitle>
          <CardDescription>
            There are no analysis results to display for this tender yet.
          </CardDescription>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {analysisResults.map((result) => (
        <Card key={result.id} className="overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between bg-gray-50 dark:bg-gray-800">
            <div>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(result.status)}
                {result.name}
              </CardTitle>
              <CardDescription className="mt-1">
                Procedure: {result.procedure_name} | Created:{" "}
                {new Date(result.created_at).toLocaleString()}
              </CardDescription>
            </div>
            <Badge
              variant={
                result.status === "COMPLETED"
                  ? "default"
                  : result.status === "FAILED"
                    ? "destructive"
                    : "secondary"
              }
            >
              {result.status}
            </Badge>
          </CardHeader>
          <CardContent className="p-0">
            <Accordion type="single" collapsible className="w-full">
              {/* Informacion General */}
              <AccordionItem value="info-general">
                <AccordionTrigger className="px-6">
                  <Info className="mr-2" /> General Information
                </AccordionTrigger>
                <AccordionContent className="px-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Requirement</TableHead>
                        <TableHead>Detail</TableHead>
                        <TableHead>Reference</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.data.informacion_general.map((item, i) => (
                        <TableRow key={i}>
                          <TableCell>{item.requisito}</TableCell>
                          <TableCell>{item.detalle}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{item.referencia}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </AccordionContent>
              </AccordionItem>

              {/* Requisitos */}
              <AccordionItem value="requisitos">
                <AccordionTrigger className="px-6">
                  <CheckCircle className="mr-2" /> Requirements
                </AccordionTrigger>
                <AccordionContent className="px-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Requirement</TableHead>
                        <TableHead>Detail</TableHead>
                        <TableHead>Reference</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.data.requisitos.map((item, i) => (
                        <TableRow key={i}>
                          <TableCell>{item.requisito}</TableCell>
                          <TableCell>{item.detalle}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{item.referencia}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </AccordionContent>
              </AccordionItem>

              {/* Criterios No Matemáticos */}
              <AccordionItem value="criterios-no-matematicos">
                <AccordionTrigger className="px-6">
                  <FileJson className="mr-2" /> Non-Mathematical Criteria
                </AccordionTrigger>
                <AccordionContent className="px-6">
                  {result.data.criterios_no_matematicos.map((criterio, i) => (
                    <Card key={i} className="mb-4">
                      <CardHeader>
                        <CardTitle>{criterio.nombre}</CardTitle>
                        <CardDescription>
                          Total points: {criterio.puntuacion_total} |{" "}
                          Reference:{" "}
                          <Badge variant="outline">
                            {criterio.referencia}
                          </Badge>
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="mb-4">{criterio.detalle}</p>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Sub-criterion</TableHead>
                              <TableHead>Detail</TableHead>
                              <TableHead>Points</TableHead>
                              <TableHead>Reference</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {criterio.subcriterios.map((sub, j) => (
                              <TableRow key={j}>
                                <TableCell>{sub.nombre}</TableCell>
                                <TableCell>{sub.detalle}</TableCell>
                                <TableCell>{sub.puntuacion}</TableCell>
                                <TableCell>
                                  <Badge variant="outline">
                                    {sub.referencia}
                                  </Badge>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>
                  ))}
                </AccordionContent>
              </AccordionItem>

              {/* Criterios Matemáticos */}
              <AccordionItem value="criterios-matematicos">
                <AccordionTrigger className="px-6">
                  <FileJson className="mr-2" /> Mathematical Criteria
                </AccordionTrigger>
                <AccordionContent className="px-6">
                  {result.data.criterios_matematicos.map((criterio, i) => (
                    <Card key={i} className="mb-4">
                      <CardHeader>
                        <CardTitle>{criterio.nombre}</CardTitle>
                        <CardDescription>
                          Points: {criterio.puntuacion} | Reference:{" "}
                          <Badge variant="outline">
                            {criterio.referencia}
                          </Badge>
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="mb-4">{criterio.detalle}</p>
                        <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-md mb-4">
                          <p className="font-mono text-center">
                            {criterio.formula.formula}
                          </p>
                          <p className="text-sm text-center italic mt-2">
                            {criterio.formula.detalle_formula}
                          </p>
                        </div>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Symbol</TableHead>
                              <TableHead>Detail</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {criterio.formula.variables.map((v, j) => (
                              <TableRow key={j}>
                                <TableCell className="font-mono">
                                  {v.simbolo}
                                </TableCell>
                                <TableCell>{v.detalle}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>
                  ))}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

