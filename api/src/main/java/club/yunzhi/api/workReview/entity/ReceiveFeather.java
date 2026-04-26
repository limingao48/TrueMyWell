package club.yunzhi.api.workReview.entity;

import java.util.ArrayList;
import java.util.List;

public class ReceiveFeather {
    private float depth;
    private float offset;
    private float magnetic_angle;
    private float magnetic_amount;
    private float magnetic_amplitude;
    private float north_orientation;
    private float high_orientation;
    private float ref_distance;

    /**
     * 北向方位（相对）
     */
    private float relative_north_orientation;

    /**
     * 相对距离
     */
    private float relative_distance;

    /**
     * 测斜相对距离
     */
    private float inclinometer_relative_distance;
    private List<ReceiveOneFeather> oneFeathers = new ArrayList<>();

    public List<ReceiveOneFeather> getOneFeathers() {
        return oneFeathers;
    }

    public void setOneFeathers(List<ReceiveOneFeather> oneFeathers) {
        this.oneFeathers = oneFeathers;
    }

    public float getOffset() {
        return offset;
    }

    public void setOffset(float offset) {
        this.offset = offset;
    }

    public float getMagnetic_angle() {
        return magnetic_angle;
    }

    public void setMagnetic_angle(float magnetic_angle) {
        this.magnetic_angle = magnetic_angle;
    }

    public float getMagnetic_amount() {
        return magnetic_amount;
    }

    public void setMagnetic_amount(float magnetic_amount) {
        this.magnetic_amount = magnetic_amount;
    }

    public float getMagnetic_amplitude() {
        return magnetic_amplitude;
    }

    public void setMagnetic_amplitude(float magnetic_amplitude) {
        this.magnetic_amplitude = magnetic_amplitude;
    }

    public float getNorth_orientation() {
        return north_orientation;
    }

    public void setNorth_orientation(float north_orientation) {
        this.north_orientation = north_orientation;
    }

    public float getHigh_orientation() {
        return high_orientation;
    }

    public void setHigh_orientation(float high_orientation) {
        this.high_orientation = high_orientation;
    }

    public float getRef_distance() {
        return ref_distance;
    }

    public void setRef_distance(float ref_distance) {
        this.ref_distance = ref_distance;
    }

    public float getDepth() {
        return depth;
    }

    public void setDepth(float depth) {
        this.depth = depth;
    }

    public float getRelative_distance() {
        return relative_distance;
    }

    public void setRelative_distance(float relative_distance) {
        this.relative_distance = relative_distance;
    }

    public float getInclinometer_relative_distance() {
        return inclinometer_relative_distance;
    }

    public void setInclinometer_relative_distance(float inclinometer_relative_distance) {
        this.inclinometer_relative_distance = inclinometer_relative_distance;
    }

    public float getRelative_north_orientation() {
        return relative_north_orientation;
    }

    public void setRelative_north_orientation(float relative_north_orientation) {
        this.relative_north_orientation = relative_north_orientation;
    }
}
