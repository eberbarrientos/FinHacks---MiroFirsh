"use client"

import { useState, useCallback } from "react"
import { Upload, FileText, AlertCircle, CheckCircle2, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { apiClient } from "@/lib/api-client"

interface UploadPortfolioModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  portfolioId: string
  onUploadSuccess?: (holdingsCount: number) => void
}

interface ValidationError {
  row: number
  field: string
  message: string
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

export function UploadPortfolioModal({
  open,
  onOpenChange,
  portfolioId,
  onUploadSuccess,
}: UploadPortfolioModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [errors, setErrors] = useState<ValidationError[]>([])
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [holdingsCount, setHoldingsCount] = useState(0)

  const resetState = () => {
    setFile(null)
    setErrors([])
    setUploadSuccess(false)
    setUploadProgress(0)
    setHoldingsCount(0)
  }

  const handleClose = () => {
    resetState()
    onOpenChange(false)
  }

  const validateFile = (file: File): string | null => {
    if (!file.name.endsWith('.csv')) {
      return "File must be a CSV file"
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`
    }
    return null
  }

  const handleFileSelect = (selectedFile: File) => {
    const error = validateFile(selectedFile)
    if (error) {
      setErrors([{ row: 0, field: "file", message: error }])
      return
    }
    setFile(selectedFile)
    setErrors([])
    setUploadSuccess(false)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }, [])

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)
    setErrors([])

    // Simulate progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => Math.min(prev + 10, 90))
    }, 200)

    try {
      const response = await apiClient.uploadFile<{
        portfolio_id: string
        holdings_count: number
        message: string
      }>(`/api/portfolios/${portfolioId}/upload-holdings`, file)

      clearInterval(progressInterval)
      setUploadProgress(100)
      setUploadSuccess(true)
      setHoldingsCount(response.holdings_count)

      if (onUploadSuccess) {
        onUploadSuccess(response.holdings_count)
      }

      // Auto-close after success
      setTimeout(() => {
        handleClose()
      }, 2000)
    } catch (error: any) {
      clearInterval(progressInterval)
      setUploadProgress(0)

      if (error.details?.errors) {
        setErrors(error.details.errors)
      } else {
        setErrors([
          {
            row: 0,
            field: "general",
            message: error.message || "Upload failed. Please try again.",
          },
        ])
      }
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Portfolio Holdings</DialogTitle>
          <DialogDescription>
            Upload a CSV file containing your portfolio holdings data
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Drag and drop area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              relative border-2 border-dashed rounded-xl p-8 transition-all duration-200
              ${
                isDragging
                  ? "border-cyan-500 bg-cyan-500/10"
                  : "border-slate-700 hover:border-slate-600"
              }
              ${file ? "bg-slate-800/50" : ""}
            `}
          >
            <input
              type="file"
              accept=".csv"
              onChange={handleFileInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={isUploading}
            />

            <div className="flex flex-col items-center justify-center space-y-3">
              {file ? (
                <>
                  <FileText className="w-12 h-12 text-cyan-500" />
                  <div className="text-center">
                    <p className="text-sm font-medium text-slate-200">
                      {file.name}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  {!isUploading && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setFile(null)
                      }}
                      className="mt-2"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Remove
                    </Button>
                  )}
                </>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-slate-400" />
                  <div className="text-center">
                    <p className="text-sm font-medium text-slate-200">
                      Drop your CSV file here, or click to browse
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Maximum file size: 10MB
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Upload progress */}
          <AnimatePresence>
            {isUploading && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Uploading...</span>
                  <span className="text-cyan-500">{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Success message */}
          <AnimatePresence>
            {uploadSuccess && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center space-x-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl"
              >
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-emerald-500">
                    Upload successful!
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {holdingsCount} holdings uploaded
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Validation errors */}
          <AnimatePresence>
            {errors.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-2 max-h-48 overflow-y-auto"
              >
                <div className="flex items-start space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-2">
                    <p className="text-sm font-medium text-red-500">
                      Validation errors found
                    </p>
                    <div className="space-y-1">
                      {errors.slice(0, 10).map((error, index) => (
                        <p key={index} className="text-xs text-slate-400">
                          {error.row > 0 && `Row ${error.row}: `}
                          {error.field && `${error.field} - `}
                          {error.message}
                        </p>
                      ))}
                      {errors.length > 10 && (
                        <p className="text-xs text-slate-500 italic">
                          ... and {errors.length - 10} more errors
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* CSV format help */}
          <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
            <p className="text-xs font-medium text-slate-300 mb-2">
              Required CSV columns:
            </p>
            <p className="text-xs text-slate-400 font-mono">
              asset_id, asset_name, asset_type, issuer_name, sector, country,
              latitude, longitude, market_value
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Optional: state_region, revenue_exposure_pct, carbon_intensity_proxy,
              insurance_dependency_score, supply_chain_dependency_score
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex justify-end space-x-3 pt-2">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || isUploading || uploadSuccess}
            >
              {isUploading ? "Uploading..." : "Upload"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
