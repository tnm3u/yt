#!/bin/bash
# Streamlink YouTube Live Player
# Usage: ./streamlink_playlist.sh [channel_number] [quality]
#        ./streamlink_playlist.sh [quality] (plays all sequentially)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if streamlink is installed
if ! command -v streamlink &> /dev/null; then
    echo -e "${RED}❌ Streamlink is not installed!${NC}"
    echo -e "Install with: ${YELLOW}pip install streamlink${NC}"
    exit 1
fi

# Check if VLC is installed
if ! command -v vlc &> /dev/null; then
    echo -e "${YELLOW}⚠️ VLC not found, will use default player${NC}"
    PLAYER=""
else
    PLAYER="--player vlc"
fi

# Channel list (add all your channels here)
CHANNELS=(
    "AriseNewsChannel:https://www.youtube.com/@AriseNewsChannel/live"
    "TVCNewsNigeria:https://www.youtube.com/@TVCNewsNigeria/live"
    "ChannelsTelevision:https://www.youtube.com/@ChannelsTelevision/live"
    "NewsCentralAfrica:https://www.youtube.com/@NewsCentralAfrica/live"
    "NTALive:https://www.youtube.com/@NTALive/live"
    "SilverbirdN24Live:https://www.youtube.com/@SilverbirdN24Live/live"
    "AITLivestream1:https://www.youtube.com/@AITLivestream1/live"
    "VOP903FM:https://www.youtube.com/@VOP903FM/live"
)

# Quality selection
QUALITY="${2:-best}"  # Default to best quality if not specified

# Function to play a single channel
play_channel() {
    local name="$1"
    local url="$2"
    local quality="$3"
    
    echo -e "\n${BLUE}▶️ Playing:${NC} $name"
    echo -e "${YELLOW}  Quality: $quality${NC}"
    echo -e "${YELLOW}  URL: $url${NC}"
    
    # Test if channel is live first
    if streamlink --json "$url" 2>/dev/null | grep -q "streams"; then
        streamlink $PLAYER "$url" "$quality" &
        return 0
    else
        echo -e "${RED}  ❌ Channel not currently live${NC}"
        return 1
    fi
}

# Display header
echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Streamlink YouTube Live Player   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
echo ""

# If channel number provided, play only that channel
if [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge 1 ] && [ "$1" -le ${#CHANNELS[@]} ]; then
    CHANNEL_NUM=$1
    QUALITY="${2:-best}"
    
    IFS=':' read -r name url <<< "${CHANNELS[$((CHANNEL_NUM-1))]}"
    play_channel "$name" "$url" "$QUALITY"
    wait
    exit 0
fi

# If quality provided as first argument (e.g., ./script.sh 1080p)
if [[ "$1" =~ ^(best|1080p|720p|480p|360p|audio)$ ]]; then
    QUALITY="$1"
    echo -e "${GREEN}Playing ALL channels with quality: $QUALITY${NC}\n"
    
    for channel in "${CHANNELS[@]}"; do
        IFS=':' read -r name url <<< "$channel"
        play_channel "$name" "$url" "$QUALITY"
        sleep 3  # Delay between channel starts
    done
    
    wait
    exit 0
fi

# Default: Show menu and play selected channel
echo -e "${GREEN}Available Channels:${NC}"
for i in "${!CHANNELS[@]}"; do
    IFS=':' read -r name url <<< "${CHANNELS[$i]}"
    echo -e "  ${YELLOW}$((i+1)).${NC} $name"
done

echo -e "\n${BLUE}Options:${NC}"
echo -e "  • Enter ${YELLOW}number${NC} to play a single channel"
echo -e "  • Enter ${YELLOW}quality${NC} (best/1080p/720p/480p) to play all"
echo -e "  • Press ${YELLOW}Ctrl+C${NC} to stop\n"

read -p "Select option: " OPTION

if [[ "$OPTION" =~ ^[0-9]+$ ]] && [ "$OPTION" -ge 1 ] && [ "$OPTION" -le ${#CHANNELS[@]} ]; then
    IFS=':' read -r name url <<< "${CHANNELS[$((OPTION-1))]}"
    play_channel "$name" "$url" "$QUALITY"
    wait
else
    # Treat as quality string
    QUALITY="$OPTION"
    echo -e "\n${GREEN}Playing ALL channels with quality: $QUALITY${NC}"
    
    for channel in "${CHANNELS[@]}"; do
        IFS=':' read -r name url <<< "$channel"
        play_channel "$name" "$url" "$QUALITY"
        sleep 3
    done
    
    wait
fi

echo -e "\n${GREEN}✅ Done${NC}"
