package club.yunzhi.api.workReview.entity;

import com.fasterxml.jackson.annotation.JsonView;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@SQLDelete(sql = "update `feather` set deleted = 1 where id = ?")
@Where(clause = "deleted = false")
public class Feather extends BaseEntity {
    /**
     * 深度
     */
    private float depth;
    private float x0;
    private float y0;
    private float z0;
    private float x1;
    private float y1;
    private float z1;
    private float x2;
    private float y2;
    private float z2;
    private float g_x;
    private float g_y;
    private float g_z;
    private float r_angle;
    private float l_angle;
    private float d_angle;
    private float temperature;
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

    @ManyToOne
    @JoinColumn(nullable = false)
    @JsonView(TaskJsonView.class)
    private Well well;

    @OneToMany(mappedBy = "feather")
    @JsonView(TaskJsonView.class)
    private List<Predict> predicts = new ArrayList<>();

    public float getG_x() {
        return g_x;
    }

    public void setG_x(float g_x) {
        this.g_x = g_x;
    }

    public float getG_y() {
        return g_y;
    }

    public void setG_y(float g_y) {
        this.g_y = g_y;
    }

    public float getG_z() {
        return g_z;
    }

    public void setG_z(float g_z) {
        this.g_z = g_z;
    }

    public float getR_angle() {
        return r_angle;
    }

    public void setR_angle(float r_angle) {
        this.r_angle = r_angle;
    }

    public float getL_angle() {
        return l_angle;
    }

    public void setL_angle(float l_angle) {
        this.l_angle = l_angle;
    }

    public float getD_angle() {
        return d_angle;
    }

    public void setD_angle(float d_angle) {
        this.d_angle = d_angle;
    }

    public float getTemperature() {
        return temperature;
    }

    public void setTemperature(float temperature) {
        this.temperature = temperature;
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



    public List<Predict> getPredicts() {
        return predicts;
    }

    public void setPredicts(List<Predict> predicts) {
        this.predicts = predicts;
    }

    //    @ManyToMany()
//    @JsonView(TaskJsonView.class)
//    private List<Task> tasks = new ArrayList<>();
    public float getDepth() {
        return depth;
    }

    public void setDepth(float depth) {
        this.depth = depth;
    }

    public float getX0() {
        return x0;
    }

    public void setX0(float x0) {
        this.x0 = x0;
    }

    public float getY0() {
        return y0;
    }

    public void setY0(float y0) {
        this.y0 = y0;
    }

    public float getZ0() {
        return z0;
    }

    public void setZ0(float z0) {
        this.z0 = z0;
    }

    public float getX1() {
        return x1;
    }

    public void setX1(float x1) {
        this.x1 = x1;
    }

    public float getY1() {
        return y1;
    }

    public void setY1(float y1) {
        this.y1 = y1;
    }

    public float getZ1() {
        return z1;
    }

    public void setZ1(float z1) {
        this.z1 = z1;
    }

    public float getX2() {
        return x2;
    }

    public void setX2(float x2) {
        this.x2 = x2;
    }

    public float getY2() {
        return y2;
    }

    public void setY2(float y2) {
        this.y2 = y2;
    }

    public float getZ2() {
        return z2;
    }

    public void setZ2(float z2) {
        this.z2 = z2;
    }

    public float getRef_distance() {
        return ref_distance;
    }

    public void setRef_distance(float ref_distance) {
        this.ref_distance = ref_distance;
    }

    public Well getWell() {
        return well;
    }

    public void setWell(Well well) {
        this.well = well;
    }

    public float getRelative_north_orientation() {
        return relative_north_orientation;
    }

    public void setRelative_north_orientation(float relative_north_orientation) {
        this.relative_north_orientation = relative_north_orientation;
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

    public interface TaskJsonView {}
}