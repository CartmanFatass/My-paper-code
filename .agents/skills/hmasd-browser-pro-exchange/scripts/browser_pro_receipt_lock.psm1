Set-StrictMode -Version Latest

if (-not ('HmasdBrowserProReceiptNative' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

public static class HmasdBrowserProReceiptNative {
    private const uint GenericRead = 0x80000000;
    private const uint FileShareRead = 0x00000001;
    private const uint OpenExisting = 3;
    private const uint FileFlagOpenReparsePoint = 0x00200000;
    private const uint FileFlagBackupSemantics = 0x02000000;

    [StructLayout(LayoutKind.Sequential)]
    private struct FileInformation {
        public uint FileAttributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
        public uint VolumeSerialNumber;
        public uint FileSizeHigh;
        public uint FileSizeLow;
        public uint NumberOfLinks;
        public uint FileIndexHigh;
        public uint FileIndexLow;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFileW(
        string fileName,
        uint desiredAccess,
        uint shareMode,
        IntPtr securityAttributes,
        uint creationDisposition,
        uint flagsAndAttributes,
        IntPtr templateFile);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandle(
        SafeFileHandle handle, out FileInformation information);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetFinalPathNameByHandleW(
        SafeFileHandle handle, StringBuilder path, uint pathLength, uint flags);

    public static SafeFileHandle OpenReadNoFollow(string path) {
        SafeFileHandle handle = CreateFileW(
            path,
            GenericRead,
            FileShareRead,
            IntPtr.Zero,
            OpenExisting,
            FileFlagOpenReparsePoint | FileFlagBackupSemantics,
            IntPtr.Zero);
        if (handle.IsInvalid) {
            int error = Marshal.GetLastWin32Error();
            handle.Dispose();
            throw new Win32Exception(error);
        }
        return handle;
    }

    public static uint GetAttributes(SafeFileHandle handle) {
        FileInformation information;
        if (!GetFileInformationByHandle(handle, out information)) {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
        return information.FileAttributes;
    }

    public static string GetFinalPath(SafeFileHandle handle) {
        uint capacity = 512;
        while (true) {
            var path = new StringBuilder((int)capacity);
            uint length = GetFinalPathNameByHandleW(handle, path, capacity, 0);
            if (length == 0) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            if (length < capacity) {
                return path.ToString();
            }
            if (length == UInt32.MaxValue) {
                throw new InvalidOperationException("Final receipt path is too long");
            }
            capacity = length + 1;
        }
    }
}
'@
}

function Get-HmasdBrowserProSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        return -join @($hasher.ComputeHash($Bytes) | ForEach-Object { $_.ToString('x2') })
    } finally {
        $hasher.Dispose()
    }
}

function Invoke-HmasdBrowserProReceiptLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ReceiptPath,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    if ($ExpectedSha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Browser Pro expected receipt SHA-256 must be exactly 64 lowercase hexadecimal characters'
    }

    $canonicalPath = [IO.Path]::GetFullPath($ReceiptPath)
    $handle = $null
    $stream = $null
    try {
        try {
            $handle = [HmasdBrowserProReceiptNative]::OpenReadNoFollow($canonicalPath)
        } catch {
            throw "Browser Pro receipt lock/open failed: $canonicalPath"
        }

        $attributes = [HmasdBrowserProReceiptNative]::GetAttributes($handle)
        if (($attributes -band [uint32][IO.FileAttributes]::Directory) -ne 0 -or
            ($attributes -band [uint32][IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Browser Pro receipt lock requires an existing regular file without a final reparse point: $canonicalPath"
        }

        $finalPath = [HmasdBrowserProReceiptNative]::GetFinalPath($handle)
        if ($finalPath.StartsWith('\\?\UNC\', [StringComparison]::OrdinalIgnoreCase)) {
            $finalPath = '\\' + $finalPath.Substring(8)
        } elseif ($finalPath.StartsWith('\\?\', [StringComparison]::OrdinalIgnoreCase)) {
            $finalPath = $finalPath.Substring(4)
        }
        $finalPath = [IO.Path]::GetFullPath($finalPath)
        if (-not [string]::Equals($finalPath, $canonicalPath, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Browser Pro receipt resolved path does not equal its canonical path: $canonicalPath"
        }

        try {
            $stream = [IO.FileStream]::new($handle, [IO.FileAccess]::Read)
            $handle = $null
        } catch {
            throw "Browser Pro receipt lock/open failed: $canonicalPath"
        }

        $memory = [IO.MemoryStream]::new()
        try {
            $stream.CopyTo($memory)
            [byte[]]$receiptBytes = $memory.ToArray()
        } finally {
            $memory.Dispose()
        }

        $actualSha256 = Get-HmasdBrowserProSha256 $receiptBytes
        if ($actualSha256 -cne $ExpectedSha256) {
            throw "Browser Pro receipt changed between validation and locked archival: $canonicalPath"
        }

        return & $Action $receiptBytes
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
        if ($null -ne $handle) { $handle.Dispose() }
    }
}

Export-ModuleMember -Function Invoke-HmasdBrowserProReceiptLock
